import urllib.request
import json
import time

for i in range(10):
    try:
        res = urllib.request.urlopen('http://localhost:1880/api/telemetry', timeout=2)
        data = json.loads(res.read().decode('utf-8'))
        s = data.get('state', {})
        loc = s.get('fault_location', '').encode('ascii', 'ignore').decode()
        print(f"[{i}s] idx={s.get('replay_index')} replaying={s.get('is_replaying')} sev={s.get('fault_severity')} health={s.get('health_score')} loc={loc}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(1)
