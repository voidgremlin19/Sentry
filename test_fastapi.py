from backend.main import get_traces
try:
    data = get_traces()
    import json
    json.dumps(data)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
