import json
from django.core.checks.messages import Error
from django.http import HttpResponse
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render

import hashlib

from .models import *
from .userverify import verify_token

import appointment.instrument as inst_service
import appointment.room as room_service
import appointment.insttype as type_service
import appointment.usergroup as usergroup_service
import appointment.user as user_service
import appointment.price as price_service
import appointment.order as order_service
import appointment.availability as ava_service
import appointment.notice as notice_service


def index(request):
    if request.method == "POST":
        return JsonResponse(json.loads(request.body))
    return HttpResponse("index")


def testview(request):
    return render(request, 'test.html', {})


# * GET INFORMATION

def get_type(request):  # 获取所有乐器的种类列表
    if request.method == "GET":
        try:
            data = type_service.get_inst_type_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_inst(request):  # 获取所有乐器的种类列表
    if request.method == "GET":
        try:
            data = inst_service.get_inst_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_room(request):  # 获取所有乐器的种类列表
    if request.method == "GET":
        try:
            data = room_service.get_room_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_usergroup(request):  # 获取所有用户组的列表
    if request.method == "GET":
        try:
            data = usergroup_service.get_group_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# def get_user(request):  # 获取所有用户的列表
#     if request.method == "GET":
#         try:
#             data = user_service.get_user_info()
#             return HttpResponse(data)
#         except Exception as e:
#             return HttpResponse(e, status=400)
#     return HttpResponse('Method Not Allowed', status=405)


def get_price(request):  # 获取（用户，乐器，房间）三元组的价格
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            price = price_service.get_price(
                req["userpk"], req["roompk"], req["instpk"])
            if price == -1:  # 没有可用的价格规则
                return HttpResponse("no valid price", status=406)
            return HttpResponse(price)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_room_for_type(request):
    if request.method == "POST":  # 获取可用的房间
        try:
            req = json.loads(request.body)
            data = type_service.get_room_for_type(req)
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_inst_for_type(request):
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            data = inst_service.get_inst_for_type(req["typepk"])
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_order(request):
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            data = order_service.get_order(req)
            if data == "not found":
                return HttpResponse("no such order", status=404)
            if data == "empty Qset":
                return HttpResponse("should at least one query", status=416)
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_user(request):  # 获取用户
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            data = user_service.get_user(req)
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * MANAGE TYPE 乐器类型管理


def manage_type(request):  # 新建乐器类型
    try:
        if request.method == "POST":  # 增
            req = json.loads(request.body)
            typepk = InstrumentType.objects.create_type(req["name"])
            return HttpResponse(typepk)
        elif request.method == "DELETE":  # 删除乐器类型
            req = json.loads(request.body)
            ret = type_service.delete_type(req["pk"])
            if ret == "forbidden":
                return HttpResponse("cannot delete built-in type", status=403)
            elif ret == False:
                return HttpResponse("related instrument exist", status=409)
            return HttpResponse("success")
        elif request.method == "PATCH":
            req = json.loads(request.body)
            ret = type_service.update_type(req)
            if ret == "forbidden":
                return HttpResponse("cannot update built-in type", status=403)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * MANAGE INSTRUMENT 乐器管理
def manage_inst(request):  # 管理乐器
    try:
        if request.method == "POST":  # 增
            req = json.loads(request.body)
            if(req["typepk"] == 1):
                return HttpResponse("cannot add null instrument", status=403)
            des = ""
            if "description" in req:
                des = req["description"]
            instpk = Instrument.objects.create_inst(
                name=req["name"], typepk=req["typepk"], des=des)
            return HttpResponse(instpk)
        elif request.method == "DELETE":  # 删除乐器
            req = json.loads(request.body)
            ret = inst_service.delete_inst(req["pk"])
            if ret == "forbidden":
                return HttpResponse("cannot delete built-in inst", status=403)
            elif ret == "order":
                return HttpResponse("related order exist", status=409)
            return HttpResponse("success")
        elif request.method == "PATCH":  # 改
            req = json.loads(request.body)
            ret = inst_service.update_inst(req)
            if ret == "forbidden":
                return HttpResponse("cannot update built-in inst", status=403)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def manage_inst_to_room(request):
    try:
        if request.method == "POST":  # 加入乐器到房间的关系
            req = json.loads(request.body)
            ret = inst_service.add_inst_to_room(
                req["instpk"], req["roompk"])
            if ret == "exist":
                return HttpResponse("already", status=409)
            return HttpResponse("success")
        elif request.method == "DELETE":
            req = json.loads(request.body)
            ret = inst_service.remove_inst_from_room(
                req["instpk"], req["roompk"])  # 移除单个乐器与单个房间的关系
            if ret == "notexist":
                return HttpResponse("not exist", status=409)
            # TODO : 有相关订单
            return HttpResponse("success")
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

# * MANAGE ROOM  房间管理


def manage_room(request):
    try:
        if request.method == "POST":  # 创建房间
            req = json.loads(request.body)
            if "max_inst" not in req:
                req["max_inst"] = 1
            des = ""
            if "description" in req:
                des = req["description"]
            roompk = Room.objects.create_room(
                name=req["name"], max_inst=req["max_inst"], des=des)
            return HttpResponse(roompk)
        elif request.method == "DELETE":  # 删除房间
            req = json.loads(request.body)
            ret = room_service.delete_room(req["pk"])
            if ret == "forbidden":
                return HttpResponse("cannot delete built-in room", status=403)
            elif ret == "order":
                return HttpResponse("related order exist", status=409)
            return HttpResponse("success")
        elif request.method == "PATCH":  # 改
            req = json.loads(request.body)
            ret = room_service.update_room(req)
            if ret == "forbidden":
                return HttpResponse("cannot update built-in room", status=403)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * 用户组管理
def manage_usergroup(request):
    try:
        if request.method == "POST":  # 创建用户组
            req = json.loads(request.body)
            grouppk = UserGroup.objects.create_group(name=req["name"])
            return HttpResponse(grouppk)
        elif request.method == "DELETE":  # 删除用户组
            req = json.loads(request.body)
            ret = usergroup_service.delete_group(req["pk"])
            if ret == "forbidden":  # 不能删除内置用户组
                return HttpResponse("cannot delete built-in group", status=403)
            return HttpResponse("success")
        elif request.method == "PATCH":
            req = json.loads(request.body)
            ret = usergroup_service.update_group(req)
            if ret == "forbidden":
                return HttpResponse("cannot update built-in group", status=403)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * (测试用)用户管理
def manage_user(request):
    try:
        if request.method == "POST":  # 测试用 ： 创建新用户
            req = json.loads(request.body)
            ret = user_service.get_or_create_user(req)
            # TODO : 处理openid/thuid 403情况
            return HttpResponse(ret["userpk"])
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

# * 设置用户与用户组的关系


def manage_user_to_group(request):
    try:
        if request.method == "POST":  # 设置用户的用户组
            req = json.loads(request.body)
            ret = user_service.set_usergroup(req["userpk"], req["usergrouppk"])
            if ret == "exist":
                return HttpResponse("user already in this group", status=409)
            if ret == "forbidden":
                return HttpResponse("cannot manage built-in group", status=403)
            return HttpResponse(ret)
        elif request.method == "DELETE":  # 取消用户的用户组
            req = json.loads(request.body)
            ret = user_service.unset_usergroup(
                req["userpk"], req["usergrouppk"])
            if ret == "forbidden":
                return HttpResponse("cannot manage built-in group", status=403)
            if ret == "notexist":
                return HttpResponse("user not in this group", status=409)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

# * 乐器类型价格:


def manage_type_price(request):
    try:
        if request.method == "PUT":  # 设置（用户组，乐器类型）的价格
            req = json.loads(request.body)
            ret = price_service.set_type_price(
                req["usergrouppk"], req["insttypepk"], req["price"])
            return HttpResponse(ret)
        elif request.method == "GET":
            typepk = request.GET.get("insttypepk")
            ret = price_service.get_all_price_for_type(typepk)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * 房间价格
def manage_room_price(request):
    try:
        if request.method == "PUT":  # 设置（用户组，房间）的价格
            req = json.loads(request.body)
            ret = price_service.set_room_price(
                req["usergrouppk"], req["roompk"], req["price"])
            return HttpResponse(ret)
        elif request.method == "GET":
            roompk = request.GET.get("roompk")
            ret = price_service.get_all_price_for_room(roompk)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * 设置用户组与房间的特殊规则禁用

def manage_room_use(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = room_service.set_room_forbidden(req)
            if ret == "order conflict":
                return HttpResponse("order conflict", status=409)
            elif ret == "already forbidden":
                return HttpResponse("already partly forbidden", status=409)
            elif ret == "forbidden":
                return HttpResponse("cannot manage built-in room", status=403)
            return HttpResponse(ret)
        elif request.method == "DELETE":
            req = json.loads(request.body)
            ret = room_service.unset_room_forbidden(req["rulepk"])
            if ret == True:
                return HttpResponse("success")
            return HttpResponse("unknown error", status=400)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_room_forbidden(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = room_service.get_room_forbidden(req)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * 设置乐器实例的特殊规则禁用

def manage_inst_use(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = inst_service.set_inst_forbidden(req)
            if ret == "order conflict":
                return HttpResponse("order conflict", status=409)
            elif ret == "already forbidden":
                return HttpResponse("already partly forbidden", status=409)
            elif ret == "forbidden":
                return HttpResponse("cannot manage built-in inst", status=403)
            return HttpResponse(ret)
        elif request.method == "DELETE":
            req = json.loads(request.body)
            ret = inst_service.unset_inst_forbidden(req["rulepk"])
            if ret == True:
                return HttpResponse("success")
            return HttpResponse("unknown error", status=400)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_inst_forbidden(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = inst_service.get_inst_forbidden(req)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * 订单管理


def manage_order(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = order_service.create_order(req)
            if ret == "room forbidden" or ret == "inst forbidden" or ret == "no permission to use":
                return HttpResponse(ret, status=403)
            if ret == "room order conflict" or ret == "inst order conflict" or ret == "inst not in the room":
                return HttpResponse(ret, status=409)
            if ret == "begin time is in the past" or ret == "begin time is too far away" \
               or ret == "end time must in the same day" or ret == "too long period":
                return HttpResponse(ret, status=403)
            return HttpResponse(ret)
        elif request.method == "GET":  # TODO: only for test
            req = json.loads(request.body)
            data = order_service.get_all_order(req)
            return HttpResponse(data)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def verify_order(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = order_service.verify_order(req["order_token"])
            if ret:
                return HttpResponse("success")
            else:
                return HttpResponse("fail", status=409)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def cancel_order(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = order_service.cancel_order(req["orderpk"])
            if ret:
                return HttpResponse("success")
            else:
                return HttpResponse("fail", status=409)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def pay_order(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = order_service.pay_order(req["orderpk"])
            if ret != -1:
                return HttpResponse(ret)
            else:
                return HttpResponse("fail", status=409)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def manage_notice(request):
    try:
        if request.method == "POST":
            title = request.POST.get('title')
            content = request.POST.get('content')
            author = request.POST.get('author')
            time = request.POST.get('time')
            file = request.FILES.get('file')
            ret = notice_service.create_notice(
                title, content, author, time, file)
            return HttpResponse(ret)
        elif request.method == "GET":
            ret = notice_service.get_all_notice()
            return HttpResponse(ret)
        elif request.method == "DELETE":
            req = json.loads(request.body)
            ret = notice_service.delete_notice(req["noticepk"])
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def modify_notice(request):
    try:
        if request.method == "POST":
            noticepk = request.POST.get('noticepk')
            title = request.POST.get('title')
            content = request.POST.get('content')
            author = request.POST.get('author')
            time = request.POST.get('time')
            file = request.FILES.get('file')
            ret = notice_service.modify_notice(
                noticepk, title, content, author, time, file)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# 获取（用户，房间，时间段）内，房间的整体可用性


def get_room_availability(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            retdata = ava_service.get_room_availability(
                req["userpk"], req["roompk"], req["begin_time"], req["end_time"])
            json_data = json.dumps(retdata, ensure_ascii=False)
            return HttpResponse(json_data)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

# 获取（用户，乐器类型）内，乐器类型中每个乐器的可用性及时间


def get_type_availability(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            aval, unaval = ava_service.get_inst_avalist(
                req["userpk"], req["typepk"], req["begin_time"], req["end_time"])
            retdata = {"available": aval, "unavailable": unaval}
            json_data = json.dumps(retdata, ensure_ascii=False)
            return HttpResponse(json_data)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_inst_availability(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            aval, unaval, avalroom, unavalroom = ava_service.get_single_inst_avalist(
                req["userpk"], req["instpk"], req["begin_time"], req["end_time"])
            retdata = {"available": aval, "unavailable": unaval,
                       "available_room": avalroom, "unavailable_room": unavalroom}
            json_data = json.dumps(retdata, ensure_ascii=False)
            return HttpResponse(json_data)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

# 从时间段返回房间的状态


def get_room_from_time(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            aval, unaval = ava_service.get_room_from_time(
                req["userpk"], req["instpk"], req["begin_time"], req["end_time"])
            retdata = {"available": aval, "unavailable": unaval}
            json_data = json.dumps(retdata, ensure_ascii=False)
            return HttpResponse(json_data)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

# 从房间返回时间段的状态


def get_time_from_room(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            aval, unaval = ava_service.get_time_from_room(
                req["userpk"], req["instpk"], req["roompk"], req["begin_time"], req["end_time"])
            retdata = {"available": aval, "unavailable": unaval}
            json_data = json.dumps(retdata, ensure_ascii=False)
            return HttpResponse(json_data)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def manage_user_balance(request):
    try:
        if request.method == "PATCH":  # 给用户发钱
            req = json.loads(request.body)
            ret = user_service.add_balance(req["userpk"], req["money"])
            if ret == "forbidden":
                return HttpResponse(ret, status=403)
            return HttpResponse(ret)
        elif request.method == "GET":  # 查询用户余额
            userpk = request.GET.get("userpk")
            ret = user_service.get_balance(userpk)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_order_in_range(request):
    try:
        if request.method == "GET":  # 查询范围内订单
            begin = request.GET.get("begin")
            end = request.GET.get("end")
            ret = order_service.get_order_in_range(begin, end)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def set_room_image(request):
    if request.method == "POST":
        try:
            img = request.FILES.get('file')
            roompk = request.POST.get('roompk')
            room = Room.objects.get(pk=roompk)
            room.img = img
            room.img.name = hashlib.md5(("room_" + str(roompk)).encode(
                encoding='UTF-8')).hexdigest()[:10]+"."+img.name.split(".")[-1]
            room.save()
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def set_inst_image(request):
    if request.method == "POST":
        try:
            img = request.FILES.get('file')
            instpk = request.POST.get('instpk')
            inst = Instrument.objects.get(pk=instpk)
            inst.img = img
            inst.img.name = hashlib.md5(("inst_" + str(instpk)).encode(
                encoding='UTF-8')).hexdigest()[:10]+"."+img.name.split(".")[-1]
            inst.save()
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# +++++++++测试用+++++++++


def test_upload(request):  # 测试上传图片
    if request.method == "POST":
        try:
            img = request.FILES.get('file')
            room = Room.objects.all()[0]
            room.img = img
            room.save()
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_token(request):
    try:
        if request.method == "POST":
            req = json.loads(request.body)
            ret = verify_token(req)
            return HttpResponse(ret)
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


'''
def user(request):
    return HttpResponse(request.user)

def login(request):
    try:
        user = authenticate(username = request.POST['username'], password = request.POST['password'])
    except Exception as e:
        return HttpResponse(e)
    if user is not None:
        return HttpResponse(user)
    return HttpResponse('Failed to authenticate')

def register(request):
    try:
        curuser = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
        curprofile = UserProfile(profile = curuser, wxid = request.POST['wxid'])
        curprofile.save()
    except Exception as e:
        return HttpResponse(e)
    return HttpResponse(curprofile)
'''
