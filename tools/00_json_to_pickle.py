"""LibreDWG `dwgread -O JSON` output -> src.pkl (text is mixed-codepage; undecodable bytes replaced)."""
import json, pickle, sys
src = sys.argv[1] if len(sys.argv) > 1 else 'src.json'
d = json.loads(open(src, 'rb').read().decode('utf-8', 'replace'), strict=False)
pickle.dump(d, open('src.pkl', 'wb'))
print('objects', len(d['OBJECTS']))
