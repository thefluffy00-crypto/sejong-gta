# Keep only the named animations from a glTF animation library and drop the reference mesh,
# rebuilding the buffer so nothing unreferenced is carried along.
import json, struct, sys, io

SRC, DST = sys.argv[1], sys.argv[2]
WANT = set(sys.argv[3].split(','))

NCOMP = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}
CSIZE = {5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}

raw = open(SRC,'rb').read()
assert raw[:4]==b'glTF'
off, js, bin_ = 12, None, b''
while off < len(raw):
    ln, ty = struct.unpack('<II', raw[off:off+8]); c = raw[off+8:off+8+ln]; off += 8+ln
    if ty == 0x4E4F534A: js = json.loads(c.decode('utf-8'))
    elif ty == 0x004E4942: bin_ = c
g = js

keep_anims = [a for a in g.get('animations',[]) if a.get('name') in WANT]
missing = WANT - {a.get('name') for a in keep_anims}
if missing: sys.exit('clip not found: %s' % sorted(missing))

old_acc = g['accessors']; old_bv = g['bufferViews']
new_acc, new_bv, blob, remap = [], [], bytearray(), {}

def take(ai):
    if ai in remap: return remap[ai]
    a = old_acc[ai]
    if 'sparse' in a: sys.exit('sparse accessor unsupported')
    bv = old_bv[a['bufferView']]
    esz = NCOMP[a['type']] * CSIZE[a['componentType']]
    stride = bv.get('byteStride') or esz
    base = bv.get('byteOffset',0) + a.get('byteOffset',0)
    if stride == esz:
        data = bin_[base: base + a['count']*esz]
    else:                                        # de-interleave
        data = b''.join(bin_[base+i*stride : base+i*stride+esz] for i in range(a['count']))
    while len(blob) % 4: blob.append(0)          # bufferView offsets must stay 4-byte aligned
    new_bv.append({'buffer':0, 'byteOffset':len(blob), 'byteLength':len(data)})
    blob.extend(data)
    new_acc.append({k:v for k,v in a.items() if k in ('componentType','count','type','normalized','min','max')}
                   | {'bufferView': len(new_bv)-1, 'byteOffset': 0})
    remap[ai] = len(new_acc)-1
    return remap[ai]

for a in keep_anims:
    for s in a['samplers']:
        s['input'] = take(s['input']); s['output'] = take(s['output'])

for n in g['nodes']:                              # the library's reference body is dead weight
    n.pop('mesh', None); n.pop('skin', None)

out = {'asset': g['asset'], 'scene': g.get('scene',0), 'scenes': g['scenes'],
       'nodes': g['nodes'], 'animations': keep_anims,
       'accessors': new_acc, 'bufferViews': new_bv,
       'buffers': [{'byteLength': len(blob)}]}

jb = json.dumps(out, separators=(',',':')).encode('utf-8')
jb += b' ' * ((4 - len(jb) % 4) % 4)
bb = bytes(blob); bb += b'\0' * ((4 - len(bb) % 4) % 4)
glb = (b'glTF' + struct.pack('<II', 2, 12 + 8+len(jb) + 8+len(bb))
       + struct.pack('<II', len(jb), 0x4E4F534A) + jb
       + struct.pack('<II', len(bb), 0x004E4942) + bb)
open(DST,'wb').write(glb)
print('kept %d clips: %s' % (len(keep_anims), ', '.join(a['name'] for a in keep_anims)))
print('%.2f MB -> %.2f MB' % (len(raw)/1048576, len(glb)/1048576))

# usage:
#   python3 tools/slim_glb.py UAL1_Standard.glb models/animations.glb Idle_Loop,Walk_Loop,Jog_Fwd_Loop,Jump_Loop
