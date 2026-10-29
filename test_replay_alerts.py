import urllib.request
import json
import time

print("--- Starting Replay via API ---", flush=True)
req = urllib.request.Request('http://localhost:1880/api/replay/start', data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
res = urllib.request.urlopen(req, timeout=3)
print(f"Replay Start: {res.status} {res.read().decode()}", flush=True)

print("\n--- Monitoring 12 seconds of Prototype Replay ---", flush=True)
for i in range(12):
    time.sleep(1)
    try:
        res = urllib.request.urlopen('http://localhost:1880/api/telemetry', timeout=2)
        data = json.loads(res.read().decode('utf-8'))
        s = data.get('state', {})
        loc = s.get('fault_location', '').encode('ascii', 'ignore').decode()
        print(f"[{i+1}s] Step {s.get('replay_index')}/45 | Sev: {s.get('fault_severity')} | Health: {s.get('health_score')}% | Loc: {loc}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

print("\n--- Completed Replay Verification ---", flush=True)
