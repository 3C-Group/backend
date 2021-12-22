import json
from django.core import serializers
from functools import reduce
from .models import *
from django.db.models import Q

STUDENT_PK = 1
TEACHER_PK = 2
OTHER_PK = 3


def get_user_info():  # 获取所有用户的信息
    data = UserProfile.objects.all()  # 返回dict格式的objects all

    userdata = [user.get_dict() for user in data]

    json_data = json.dumps(userdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def get_user(req):
    Qset = set()
    if "thuid" in req:
        Qset.add(Q(thuid=req["thuid"]))
    if "openid" in req:
        Qset.add(Q(openid=req["openid"]))
    if "status" in req:
        if req["status"] == "STUDENT":
            Qset.add(Q(status=UserProfile.Status.STUDENT))
        elif req["status"] == "TEACHER":
            Qset.add(Q(status=UserProfile.Status.TEACHER))
        elif req["status"] == "UNAUTHORIZED":
            Qset.add(Q(status=UserProfile.Status.UNAUTHORIZED))
        else:
            Qset.add(Q(status=UserProfile.Status.OTHER))

    if "grouppk" in req:
        data = UserGroup.objects.get(pk=req["grouppk"]).userprofile_set.all()
    else:
        data = UserProfile.objects.all()

    if(len(Qset) > 0):
        data = data.filter(reduce(lambda x, y: x & y, Qset))

    if "begin_num" in req and "end_num" in req:
        data = data.order_by(
            "openid")[int(req["begin_num"]):int(req["end_num"])]
    ret_data = [item.get_dict() for item in data]  # 格式化
    json_data = json.dumps(ret_data, ensure_ascii=False)
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
            user = UserProfile.objects.get(pk=ret["userpk"])
            if status == UserProfile.Status.STUDENT:
                studentgroup = UserGroup.objects.get(pk=STUDENT_PK)
                user.group.add(studentgroup)
            elif status == UserProfile.Status.TEACHER:
                teachergroup = UserGroup.objects.get(pk=TEACHER_PK)
                user.group.add(teachergroup)
        elif userset.count() == 1:
            ret["userpk"] = userset[0].pk
            user = UserProfile.objects.get(pk=ret["userpk"])
            user.openid = openid
            user.save()
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
            user = UserProfile.objects.get(pk=ret["userpk"])
            othergroup = UserGroup.objects.get(pk=OTHER_PK)
            user.group.add(othergroup)
            user.save()
        elif userset.count() == 1:
            ret["userpk"] = userset[0].pk
        ret["state"] = "success"
        return ret


def set_usergroup(userpk, usergrouppk):  # 设置用户到用户组
    if usergrouppk == 1 or usergrouppk == 2 or usergrouppk == 3:
        return "forbidden"
    user = UserProfile.objects.get(pk=userpk)
    if user.group.filter(pk=usergrouppk).count() > 0:  # 如果已经在用户组
        return "exist"
    usergroup = UserGroup.objects.get(pk=usergrouppk)
    user.group.add(usergroup)
    return "success"


def unset_usergroup(userpk, usergrouppk):  # 取消用户从用户组
    if usergrouppk == 1 or usergrouppk == 2 or usergrouppk == 3:
        return "forbidden"
    user = UserProfile.objects.get(pk=userpk)
    if user.group.filter(pk=usergrouppk).count() == 0:  # 如果不在这个用户组
        return "notexist"
    usergroup = UserGroup.objects.get(pk=usergrouppk)
    user.group.remove(usergroup)
    return "success"


def add_balance(userpk, money):
    if money <= 0:
        return "forbidden"
    user = UserProfile.objects.get(pk=userpk)
    user.add_balance(money)
    return "success"


def get_balance(userpk):
    return UserProfile.objects.get(pk=userpk).balance
