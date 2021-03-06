import json
from django.core import serializers
from .models import *


def get_group_info():  # 获取所有房间的信息
    data = UserGroup.objects.all()  # 返回dict格式的objects all

    groupdata = [group.get_dict() for group in data]
    retdata = {}
    retdata["groupnum"] = len(data)  # 统计数量
    retdata["data"] = groupdata  # 房间的详情信息

    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def delete_group(pk):  # 删除某一用户组
    if pk == 1 or pk == 2 or pk == 3:  # 删除内置用户组
        return "forbidden"
    group = UserGroup.objects.get(pk=pk)  # 尝试获取该用户组
    group.userprofile_set.clear()
    group.delete()
    return "success"


def update_group(req):
    pk = req["pk"]
    if pk == 1 or pk == 2 or pk == 3:
        return "forbidden"
    group = UserGroup.objects.get(pk=pk)
    if "name" in req:
        group.name = req["name"]
    group.save()
    return "success"
