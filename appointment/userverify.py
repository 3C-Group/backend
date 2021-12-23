import json
import requests
from .models import *
from .user import get_or_create_user


def verify_token(req):
    token_data = json.dumps({"token": req["token"]}, ensure_ascii=False)
    url = "https://alumni-test.iterator-traits.com/fake-id-tsinghua-proxy/api/user/session/token"
    try:
        res = requests.post(url=url, data=token_data, headers={
                            'content-type': "application/json"})
        data = res.json()
        t = {"openid": req["openid"]}
        if "user" in data:
            t["thuid"] = data["user"]["card"]
            t["authorized"] = True
            ret = get_or_create_user(t)
            return json.dumps({"userpk": ret["userpk"], "status": "STUDENT", "detail": data})
        else:
            t["authorized"] = False
            ret = get_or_create_user(t)
            return json.dumps({"userpk": ret["userpk"], "status": "OTHER"})
    except:
        return json.dumps({"status": "failed"})
