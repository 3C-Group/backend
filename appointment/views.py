import json
from django.core import serializers
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model

from .models import *

import appointment.instrument as inst_service

User = get_user_model()

def index(request):
    if request.method == "POST":
        return JsonResponse(json.loads(request.body))
    return HttpResponse("index")

def testview(request):
    return render(request, 'test.html', {} )

# * GET INFORMATION

def get_type(request):  # 获取所有乐器的种类列表
    if request.method == "GET":
        try:
            data = inst_service.get_inst_type_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

def get_inst(request):  # 获取所有乐器的种类列表
    if request.method == "GET":
        try:
#            data = inst_service.get_inst_type()
            data = inst_service.get_inst_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

def get_room(request):  # 获取所有乐器的种类列表
    if request.method == "GET":
        try:
            data = inst_service.get_room_info()
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * MANAGE TYPE 乐器类型管理


def add_type(request):  # 新建乐器类型
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            typepk = InstrumentType.objects.create_type(req["name"])
            return HttpResponse(typepk)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


def delete_type(request):  # 删除某个乐器类型
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            flag = inst_service.delete_type(req["pk"])
            if flag == False:
                return HttpResponse("存在属于该类型的乐器", status=401)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * MANAGE INSTRUMENT 乐器管理
def add_inst(request):  # 创建乐器
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            instpk = Instrument.objects.create_inst(name = req["name"], typepk = req["typepk"])
            return HttpResponse(instpk)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

def delete_inst(request): # 删除乐器
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            ret = inst_service.delete_inst(req["pk"])
            if ret == "order":
                return HttpResponse("存在有关该乐器的订单尚未完成", status=401)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

def add_inst_to_room(request): # 使得某一个inst可以前往room
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            ret = inst_service.add_inst_to_room(req["instpk"], req["roompk"])
            if ret == "exist":
                return HttpResponse("这个乐器已经可以前往该房间了", status=401)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

def remove_inst_from_room(request): # 删除某一个inst可以前往room的关系
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            ret = inst_service.add_inst_to_room(req["instpk"], req["roompk"])
            if ret == "notexist":
                return HttpResponse("这个乐器本来就不能前往该房间", status=401)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

def remove_inst_from_all(request): # 清理该乐器可以去的所有房间关系
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            ret = inst_service.remove_inst_from_all(req["instpk"])
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# * MANAGE ROOM  房间管理
def add_room(request):  # 创建乐器
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            if "max_inst" not in req:
                req["max_inst"] = 1
            roompk = Room.objects.create_room(name = req["name"], max_inst = req["max_inst"])
            return HttpResponse(roompk)
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)

def delete_room(request): # 删除乐器
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            ret = inst_service.delete_room(req["pk"])
            if ret == "order":
                return HttpResponse("存在有关该房间的订单尚未完成", status=401)
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status=400)
    return HttpResponse('Method Not Allowed', status=405)


# +++++++++测试用+++++++++
def test_upload(request): # 测试上传图片
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
