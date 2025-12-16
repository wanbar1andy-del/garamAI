import requests
import json
import sys

BASE_URL = "http://localhost:5004"

def test_history():
    print(f"Testing History at {BASE_URL}/api/simulation/history")
    try:
        resp = requests.get(f"{BASE_URL}/api/simulation/history")
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Data type: {type(data)}")
            if isinstance(data, list):
                print(f"Count: {len(data)}")
                if len(data) > 0:
                    print(f"First: {data[0]}")
                    print(f"Last: {data[-1]}")
            else:
                print(f"Data: {data}")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_history()
