import urllib.request
import json
import time

print("=" * 60)
print("AC DIGITAL TWIN: FULL PROTOTYPE REPLAY & TELEGRAM TEST")
print("=" * 60)

# 1. Start Replay
req = urllib.request.Request('http://localhost:1880/api/replay/start', data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
res = urllib.request.urlopen(req)
print(f"[REPLAY STARTED] Status: {res.status}")

# 2. Track 45-second lifecycle
observed_phases = set()
start_time = time.time()

for second in range(1, 46):
    time.sleep(1)
    try:
        r = urllib.request.urlopen('http://localhost:1880/api/telemetry', timeout=2)
        d = json.loads(r.read().decode('utf-8'))
        s = d.get('state', {})
        idx = s.get('replay_index', 0)
        sev = s.get('fault_severity', 'UNKNOWN')
        health = s.get('health_score', 0)
        loc = s.get('fault_location', '').encode('ascii', 'ignore').decode()
        
        phase_num = ((idx - 1) // 5) + 1 if idx > 0 else 0
        if loc not in observed_phases and loc != "":
            observed_phases.add(loc)
            print(f"[{second:02d}s] >>> NEW PHASE {phase_num} DETECTED: {loc} | Health: {health}% | Sev: {sev} <<<", flush=True)
        else:
            print(f"[{second:02d}s] Step {idx:02d}/45 (Phase {phase_num}) | Health: {health:3d}% | {loc[:40]}", flush=True)
            
    except Exception as e:
        print(f"[{second:02d}s] Error: {e}", flush=True)

print("=" * 60)
print(f"VERIFICATION COMPLETE: Observed {len(observed_phases)} distinct diagnostic phases.")
print("=" * 60)
