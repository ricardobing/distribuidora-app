import requests

url = 'http://localhost:8000/api/v1/auth/login'
creds = {'email': 'admin@molymarket.com', 'password': 'admin1234'}
try:
    r = requests.post(url, json=creds, timeout=10)
    print('STATUS', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
except Exception as e:
    print('ERROR', str(e))
