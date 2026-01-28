import requests

def fetch_data(url):
    r = requests.get(url)
    return r.json()
