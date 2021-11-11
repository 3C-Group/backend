import json
from django.core import serializers
from .models import *


def get_user_info():  # 获取所有房间的信息
    data = serializers.serialize(
        "python", UserProfile.objects.all())  # 返回dict格式的objects all

    userdata = []
    for user in data:  # 统计数量，房间信息的详情信息
        userinfo = {}
        userinfo["pk"] = user["pk"]
        userinfo["balance"] = user["fields"]["balance"]
        userinfo["usergroup"] = user["fields"]["group"]
        userinfo["status"] = user["fields"]["status"]
        userinfo["openid"] = user["fields"]["openid"]
        userinfo["thuid"] = user["fields"]["thuid"]
        userdata.append(userinfo)

    json_data = json.dumps(userdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def get_or_create_user(req):
    # TODO:  验证openid的真实性
    # if openid not valid ; return ret["state"] = "notvalid"
    openid = req["openid"]  # 测试用, 实际应从某处获取openid

    ret = {}
    if req["authorized"] == True:
        thuid = req["thuid"]
        status = UserProfile.Status.STUDENT
        # TODO : (FOR TEST)假设现在可用的都是学生
        # TODO : 验证thuid的真实性

        userset = UserProfile.objects.filter(
            thuid=thuid)  # 筛选出账户中所有持有相同thuid的用户
        if userset.count() > 1:
            raise ValueError("more than one users have same thuid")

        if userset.count() == 0:
            ret["userpk"] = UserProfile.objects.create_user(
                openid, status, thuid)
        elif userset.count() == 1:
            ret["userpk"] = userset.get(0).pk
        ret["state"] = "success"
        return ret
    else:
        status = UserProfile.Status.UNAUTHORIZED
        userset = UserProfile.objects.filter(status=status)  # 筛选出未认证身份的用户
        userset = userset.filter(openid=openid)  # 筛选出对应openid的用户
        if userset.count() > 1:
            raise ValueError("more than one users have same openid")

        if userset.count() == 0:
            ret["userpk"] = UserProfile.objects.create_user(openid, status)
        elif userset.count() == 1:
            ret["userpk"] = userset[0].pk
        ret["state"] = "success"
        return ret


def set_usergroup(userpk, usergrouppk):  # 设置用户到用户组
    user = UserProfile.objects.get(pk=userpk)
    if user.group.filter(pk=usergrouppk).count() > 0:  # 如果已经在用户组
        return "exist"
    usergroup = UserGroup.objects.get(pk=usergrouppk)
    user.group.add(usergroup)
    return "success"


def unset_usergroup(userpk, usergrouppk):  # 取消用户从用户组
    user = UserProfile.objects.get(pk=userpk)
    if user.group.filter(pk=usergrouppk).count() == 0:  # 如果不在这个用户组
        return "notexist"
    usergroup = UserGroup.objects.get(pk=usergrouppk)
    user.group.remove(usergroup)
    return "success"
