import json
from django.core.checks.messages import Error
from django.http import HttpResponse
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render

from .models import *

import appointment.instrument as inst_service
import appointment.room as room_service
import appointment.insttype as type_service
import appointment.usergroup as usergroup_service
import appointment.user as user_service
import appointment.price as price_service


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


def get_user(request):  # 获取所有用户的列表
    if request.method == "GET":
        try:
            data = user_service.get_user_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def get_price(request):  # 获取（用户，乐器，房间）三元组的价格
    if request.method == "GET":
        try:
            req = json.loads(request.body)
            price = price_service.get_price(
                req["userpk"], req["instpk"], req["roompk"])
            if price == -1:  # 没有可用的价格规则
                return HttpResponse("no valid price", status=202)
            return HttpResponse(price)
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
            flag = type_service.delete_type(req["pk"])
            if flag == False:
                return HttpResponse("related instrument exist", status=409)
            return HttpResponse("success")
    except Exception as e:
        return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * MANAGE INSTRUMENT 乐器管理
def manage_inst(request):  # 管理乐器
    try:
        if request.method == "POST":  # 增
            req = json.loads(request.body)
            instpk = Instrument.objects.create_inst(
                name=req["name"], typepk=req["typepk"])
            return HttpResponse(instpk)
        elif request.method == "DELETE":  # 删除乐器类型
            req = json.loads(request.body)
            ret = inst_service.delete_inst(req["pk"])
            if ret == "order":
                return HttpResponse("related order exist", status=409)
            return HttpResponse("success")
        elif request.method == "PATCH":  # 改
            req = json.loads(request.body)
            return HttpResponse(inst_service.update_inst(req))
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
            roompk = Room.objects.create_room(
                name=req["name"], max_inst=req["max_inst"])
            return HttpResponse(roompk)
        elif request.method == "DELETE":  # 删除房间
            req = json.loads(request.body)
            ret = room_service.delete_room(req["pk"])
            if ret == "order":
                return HttpResponse("related order exist", status=409)
            return HttpResponse("success")
        elif request.method == "PATCH":  # 改
            req = json.loads(request.body)
            return HttpResponse(room_service.update_room(req))
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
                return HttpResponse("cannot delete built-in groups", status=403)
            # TODO: 检查是否存在对应的用户
            #            if ret == "order":
            #                return HttpResponse("related user exist", status=409)
            return HttpResponse("success")
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
            req = json.loads(request.body)
            ret = price_service.get_all_price_for_type(req["insttypepk"])
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
            req = json.loads(request.body)
            ret = price_service.get_all_price_for_room(req["roompk"])
            return HttpResponse(ret)
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
