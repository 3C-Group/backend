import json
from django.core import serializers
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model

from .models import *

import appointment.instrument as inst_service
import appointment.room as room_service
import appointment.insttype as type_service
import appointment.usergroup as usergroup_service

User = get_user_model()


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


# * MANAGE TYPE 乐器类型管理
def manage_type(request):  # 新建乐器类型
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            typepk = InstrumentType.objects.create_type(req["name"])
            return HttpResponse(typepk)
        except Exception as e:
            return HttpResponse(e, status=400)
    elif request.method == "DELETE":  # 删除乐器类型
        try:
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
    if request.method == "POST":  # 增
        try:
            req = json.loads(request.body)
            instpk = Instrument.objects.create_inst(
                name=req["name"], typepk=req["typepk"])
            return HttpResponse(instpk)
        except Exception as e:
            return HttpResponse(e, status=400)
    elif request.method == "DELETE":  # 删除乐器
        try:
            req = json.loads(request.body)
            ret = inst_service.delete_inst(req["pk"])
            if ret == "order":
                return HttpResponse("related order exist", status=409)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def manage_inst_to_room(request):
    if request.method == "POST":  # 加入乐器到房间的关系
        try:
            req = json.loads(request.body)
            ret = inst_service.add_inst_to_room(
                req["instpk"], req["roompk"])
            if ret == "exist":
                return HttpResponse("already", status=409)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    elif request.method == "DELETE":
        try:
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
    if request.method == "POST":  # 创建房间
        try:
            req = json.loads(request.body)
            if "max_inst" not in req:
                req["max_inst"] = 1
            roompk = Room.objects.create_room(
                name=req["name"], max_inst=req["max_inst"])
            return HttpResponse(roompk)
        except Exception as e:
            return HttpResponse(e, status=400)
    elif request.method == "DELETE":  # 删除房间
        try:
            req = json.loads(request.body)
            ret = room_service.delete_room(req["pk"])
            if ret == "order":
                return HttpResponse("related order exist", status=409)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * 用户组管理
def manage_usergroup(request):
    if request.method == "POST":  # 创建用户组
        try:
            req = json.loads(request.body)
            grouppk = UserGroup.objects.create_group(name=req["name"])
            return HttpResponse(grouppk)
        except Exception as e:
            return HttpResponse(e, status=400)
    elif request.method == "DELETE":  # 删除用户组
        try:
            req = json.loads(request.body)
            ret = usergroup_service.delete_group(req["pk"])
            # TODO: 检查是否存在对应的用户
            #            if ret == "order":
            #                return HttpResponse("related user exist", status=409)
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
