import requests
import json
import sys

BASE_URL = "http://localhost:5004"

endpoints = [
    "/api/simulation/today",
    "/api/simulation/history",
    "/api/live/portfolio",
    "/api/market/indices"
]

def test_api():
    print(f"Testing API at {BASE_URL}")
    try:
        # Check root or health first to ensure server is up
        r = requests.get(f"{BASE_URL}/api/live/status")
        print(f"Server Status: {r.status_code}")
    except Exception as e:
        print(f"Server not reachable: {e}")
        return

    for ep in endpoints:
        url = f"{BASE_URL}{ep}"
        print(f"\nTesting {ep}...")
        try:
            resp = requests.get(url)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'List len ' + str(len(data))}")
                    # Print snippet
                    print(str(data)[:200])
                except:
                    print(f"Response not JSON: {resp.text[:100]}")
            else:
                print(f"Error Body: {resp.text[:200]}")
        except Exception as ex:
            print(f"Exception: {ex}")

if __name__ == "__main__":
    test_api()
