import json
from django.core import serializers
from functools import reduce
from .models import *
from django.db.models import Q
from .order import cancel_order

STUDENT_PK = 1
TEACHER_PK = 2
UNAUTH_PK = 3


def get_user_info():  # 获取所有用户的信息
    data = UserProfile.objects.all()  # 返回dict格式的objects all

    userdata = [user.get_dict() for user in data]

    json_data = json.dumps(userdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def get_user(req):
    Qset = set()
    if "userpk" in req:
        Qset.add(Q(pk=req["userpk"]))
    if "thuid" in req:
        Qset.add(Q(thuid__startswith=req["thuid"]))
    if "openid" in req:
        Qset.add(Q(openid__startswith=req["openid"]))
    if "status" in req:
        if req["status"] == "STUDENT":
            Qset.add(Q(status=UserProfile.Status.STUDENT))
        elif req["status"] == "TEACHER":
            Qset.add(Q(status=UserProfile.Status.TEACHER))
        elif req["status"] == "UNAUTHORIZED":
            Qset.add(Q(status=UserProfile.Status.UNAUTHORIZED))

    if "grouppk" in req:
        data = UserGroup.objects.get(pk=req["grouppk"]).userprofile_set.all()
    else:
        data = UserProfile.objects.all()

    if(len(Qset) > 0):
        data = data.filter(reduce(lambda x, y: x & y, Qset))
    num = len(data)

    if "begin_num" in req and "end_num" in req:
        data = data.order_by(
            "openid")[int(req["begin_num"]):int(req["end_num"])]
    ret_data = [item.get_dict() for item in data]  # 格式化
    ret_data.append(num)
    json_data = json.dumps(ret_data, ensure_ascii=False)
    return json_data


def get_or_create_user(req):
    openid = req["openid"]

    ret = {}
    if req["authorized"] == True:

        open_user_set = UserProfile.objects.filter(openid=openid)

        if open_user_set.count() != 1:
            raise ValueError("more than one users have same openid")
        open_user = open_user_set[0]
        thuid = req["thuid"]
        status = UserProfile.Status.STUDENT
        # TODO : 限于API限制，现在可用的都是学生

        userset = UserProfile.objects.filter(
            thuid=thuid)  # 筛选出账户中所有持有相同thuid的用户
        if userset.count() > 1:
            raise ValueError("more than one users have same thuid")

        if userset.count() == 0:
            ret["userpk"] = open_user.pk
            unauthgroup = UserGroup.objects.get(pk=UNAUTH_PK)
            open_user.group.remove(unauthgroup)
            if status == UserProfile.Status.STUDENT:
                studentgroup = UserGroup.objects.get(pk=STUDENT_PK)
                open_user.group.add(studentgroup)
                open_user.status = UserProfile.Status.STUDENT
                open_user.thuid = thuid
                open_user.save()
            elif status == UserProfile.Status.TEACHER:
                teachergroup = UserGroup.objects.get(pk=TEACHER_PK)
                open_user.group.add(teachergroup)
                open_user.status = UserProfile.Status.TEACHER
                open_user.thuid = thuid
                open_user.save()
        elif userset.count() == 1:
            # 修改openid
            user = userset[0]
            ret["userpk"] = user.pk
            user.openid = openid
            user.save()

            # 将用户信息从未验证向已验证迁移
            del_order = []
            for order in open_user.order_set.all():
                if order.status == Order.Status.PAID:  # 不能有已支付的订单
                    raise ValueError("paid orders exist")
                else:  # 其他订单进行迁移
                    order.user = user
                    order.save()
                    if order.status == Order.Status.UNPAID:  # 强制取消所有未支付的订单
                        del_order.append(order)

            for order in del_order:  # 强制取消所有未支付的订单
                cancel_order(order.pk)

            add_balance(user.pk, open_user.balance)  # 合并余额
            open_user.delete()

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
            unauthgroup = UserGroup.objects.get(pk=UNAUTH_PK)
            user.group.add(unauthgroup)
            user.save()
        elif userset.count() == 1:
            ret["userpk"] = userset[0].pk
        ret["state"] = "success"
        return ret


def user_unbind(openid):
    userset = UserProfile.objects.filter(openid=openid)
    if userset.count() == 0:
        return False, "no user with this openid"
    if userset.count() > 1:
        return False, "more than one users with this openid"
    user = userset[0]
    if user.status != UserProfile.Status.UNAUTHORIZED:
        user.openid = "default-openid"
        user.save()
    else:
        return False, "user with this openid is unauthorized"
    user = get_or_create_user({"openid": openid, "authorized": False})
    return True, user["userpk"]


def get_user_from_openid(openid):
    userset = UserProfile.objects.filter(openid=openid)
    if userset.count() > 1:
        return False, "more than one users with this openid"
    if userset.count() == 1:
        return True, userset[0].pk
    ret = get_or_create_user({"openid": openid, "authorized": False})
    return True, ret["userpk"]


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
