import os
import time
import urllib.request
import json

def main():
    api = os.environ.get('API_URL', 'http://localhost:8000')
    print(f'Worker starting, API URL: {api}')

    # Wait for API to be ready
    time.sleep(3)

    # Try to generate demo report
    try:
        data = json.dumps({"project_id": "proj-routerlab", "title": "Demo Report - ROUTER-LAB"}).encode('utf-8')
        req = urllib.request.Request(
            f"{api}/reports/generate",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f'Worker: generated demo report {result}')
    except Exception as e:
        print(f'Worker: error contacting api - {e}')

    print('Worker: completed startup tasks')

if __name__ == '__main__':
    main()
