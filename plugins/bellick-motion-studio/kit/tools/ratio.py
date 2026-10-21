"""Match the output canvas to the source video's shape (rotation-aware).
python3 -I ratio.py <video>  ->  {"src":[w,h],"design":[W,H],"4k":[W2,H2],"orientation":...}
Design size keeps the source aspect with the SHORT side = 1080 (even numbers); 4K = design x2."""
import sys, json, subprocess
v = sys.argv[1]
info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:stream_side_data=rotation:stream_tags=rotate',
                                  '-of', 'json', v], capture_output=True, text=True).stdout)['streams'][0]
w, h = info['width'], info['height']
rot = 0
for sd in info.get('side_data_list', []) or []:
    if 'rotation' in sd: rot = int(sd['rotation'])
rot = rot or int((info.get('tags') or {}).get('rotate', 0))
if abs(rot) % 180 == 90: w, h = h, w
even = lambda x: int(round(x / 2)) * 2
if w <= h: W, H = 1080, even(1080 * h / w)
else: W, H = even(1080 * w / h), 1080
ori = 'portrait' if H > W * 1.15 else 'landscape' if W > H * 1.15 else 'square'
print(json.dumps({'src': [w, h], 'rotation': rot, 'design': [W, H], '4k': [W * 2, H * 2], 'orientation': ori}))
