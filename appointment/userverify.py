import json
import requests


def verify_token(token):
    token_data = json.dumps({"token": token}, ensure_ascii=False)
    url = "https://alumni-test.iterator-traits.com/fake-id-tsinghua-proxy/api/user/session/token"
    try:
        res = requests.post(url=url, data=token_data)
        return json.dumps(res.json())
    except:
        return False
