import sys, json, wave
import numpy as np, onnxruntime as ort
import os
MD=os.environ.get('KIT_MODELS', os.path.expanduser('~/.motion-studio/models'))
vocab=json.load(open(os.path.join(MD,'kokoro_config.json')))['vocab']
sess=ort.InferenceSession(os.path.join(MD,'kokoro-v1.0.onnx'),providers=['CPUExecutionProvider'])
ins={i.name:i for i in sess.get_inputs()}
tok_name='input_ids' if 'input_ids' in ins else 'tokens'
voices=np.load(os.path.join(MD,'voices-v1.0.bin'))
voice=sys.argv[1]; speed=float(sys.argv[2]); out=sys.argv[3]; LINES=sys.argv[4] if len(sys.argv)>4 else 'lines.json'
lines=json.load(open(LINES))
res={}
for key,ph in lines.items():
    bad=[c for c in ph if c not in vocab]
    if bad: print('UNKNOWN',key,bad)
    toks=[vocab[c] for c in ph if c in vocab]
    style=voices[voice][len(toks)-1]
    sp=np.array([speed],dtype=np.float32) if ins['speed'].type=='tensor(float)' else np.array([int(speed)],dtype=np.int32)
    a=sess.run(None,{tok_name:np.array([[0,*toks,0]],dtype=np.int64),'style':style.astype(np.float32),'speed':sp})[0].squeeze()
    np.save(f'{out}_{key}.npy',a.astype(np.float32)); res[key]=round(len(a)/24000,2)
print(json.dumps(res))
