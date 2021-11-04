import json
from django.core import serializers
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model
from .models import *

User = get_user_model()

def index(request):
    if request.method == "POST":
        return JsonResponse(json.loads(request.body))
    return HttpResponse("index")

def type(request):
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            type = InstrumentType.objects.create_type(req["name"])
            # type.save()
            return HttpResponse("success")
        except Exception as e:
            return HttpResponse(e, status = 400)
    return HttpResponse('Method Not Allowed', status=405)

def get_type(request):
    if request.method == "GET":
        try:
            data = serializers.serialize("json", InstrumentType.objects.all())
            return HttpResponse(data)
        except Exception as e:
            return HttpResponse(e, status = 400)
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