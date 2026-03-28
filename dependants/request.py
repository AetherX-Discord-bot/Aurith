import requests

API_URL = "http://104.236.25.60:3072/api"
def send_request(payload):
    try:
        requests.post(API_URL, json=payload, headers={'User-Agent': 'PyBot'}, timeout=5)
    except:
        pass