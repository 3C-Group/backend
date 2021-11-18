import json
from django.core import serializers
from .models import *


def get_inst_type_info():  # 获取所有乐器类型的信息
    data = serializers.serialize(
        "python", InstrumentType.objects.all())  # 返回dict格式的objects all

    typedata = []
    for type in data:  # 统计数量，乐器信息的详情信息
        typeinfo = {}
        typeinfo["pk"] = type["pk"]
        typeinfo["name"] = type["fields"]["name"]
        typedata.append(typeinfo)

    retdata = {}
    retdata["typenum"] = len(data)  # 统计数量
    retdata["data"] = typedata  # 乐器类型的详情信息

    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def update_type(req):
    pk = req["pk"]
    if pk == 1:
        return "forbidden"
    type = InstrumentType.objects.get(pk=req["pk"])  # 尝试获取该乐器
    if "name" in req:
        type.name = req["name"]
    type.save()
    return "success"


def delete_type(pk):  # 删除某一乐器类型
    if(pk == 1):
        return "forbidden"
    type = InstrumentType.objects.get(pk=pk)  # 尝试获取该乐器类型
    if type.instrument_set.count() != 0:  # 检查是否有该类的乐器存在
        return False  # 如果当前存在该类型乐器，不能删除
    type.delete()
    return True
