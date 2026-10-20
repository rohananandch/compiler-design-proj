import urllib.request, json

data = json.dumps({'regex': '(a|b)*abb'}).encode()
req = urllib.request.Request('http://127.0.0.1:8080/api/convert', data=data,
                             headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req, timeout=10) as r:
    resp = json.loads(r.read())

d = resp['data']
print('Reductions keys:', list(d['metrics']['reductions'].keys()))
print('Counts:', json.dumps(d['metrics']['counts'], indent=2))
print()
print('--- Construction steps ---')
for s in d['nfa']['construction_steps']:
    print(f"  Step {s['step_number']}: {s['title']}")
print()
print('--- First step NFA ---')
s0 = d['nfa']['construction_steps'][0]
print('  States:', s0['nfa']['states'])
print('  Transitions:', s0['nfa']['transitions'])
print('  Positions:', s0['nfa']['positions'])
print()
print('--- DFA states sample ---')
for st in d['dfa']['states'][:3]:
    print(' ', st)
print()
print('--- MinDFA ---')
print('  States:', [s['id'] for s in d['min_dfa']['states']])
print('  Partition mapping:', d['min_dfa'].get('partition_mapping'))
