import json
from django.core import serializers
from .models import *
from django.db.models import Q


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


def get_inst_info():  # 获取所有乐器的信息
    data = serializers.serialize(
        "python", Instrument.objects.all())  # 返回dict格式的objects all

    instdata = []
    for inst in data:  # 统计数量，乐器信息的详情信息
        instinfo = {}
        instinfo["pk"] = inst["pk"]
        instinfo["name"] = inst["fields"]["name"]

        instinfo["typepk"] = inst["fields"]["type"]
        instinfo["typename"] = InstrumentType.objects.get(
            pk=instinfo["typepk"]).name  # 获取该乐器对应的乐器类型的名称

        instinfo["roompk"] = inst["fields"]["room"]
        instinfo["roomnum"] = len(instinfo["roompk"])

        instdata.append(instinfo)

    retdata = {}
    retdata["instnum"] = len(data)  # 统计数量
    retdata["data"] = instdata  # 乐器的详情信息

    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def get_room_info():  # 获取所有房间的信息
    data = serializers.serialize(
        "python", Room.objects.all())  # 返回dict格式的objects all

    roomdata = []
    for room in data:  # 统计数量，房间信息的详情信息
        roominfo = {}
        roominfo["pk"] = room["pk"]
        roominfo["name"] = room["fields"]["name"]
        roominfo["max_inst"] = room["fields"]["max_inst"]
        roomdata.append(roominfo)

    retdata = {}
    retdata["roomnum"] = len(data)  # 统计数量
    retdata["data"] = roomdata  # 房间的详情信息

    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def delete_type(pk):  # 删除某一乐器类型
    type = InstrumentType.objects.get(pk=pk)  # 尝试获取该乐器类型
    if type.instrument_set.count() != 0:  # 检查是否有该类的乐器存在
        return False  # 如果当前存在该类型乐器，不能删除
    type.delete()
    return True


def delete_inst(pk):  # 删除某一乐器
    inst = Instrument.objects.get(pk=pk)  # 尝试获取该乐器
    # 检查是否有1.即将支付，或者2.已支付但未使用的订单存在
    if inst.order_set.filter(Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID)).count() != 0:
        return "order"  # 如果当前存在这样的乐器，不能删除
    inst.delete()
    return "success"


def delete_room(pk):  # 删除某一房间
    room = Room.objects.get(pk=pk)  # 尝试获取该房间
    # 检查是否有1.即将支付，或者2.已支付但未使用的订单存在
    if room.order_set.filter(Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID)).count() != 0:
        return "order"  # 如果当前存在这样的房间，不能删除
    # TODO: 考虑该房间如果有乐器，这些乐器应该怎么删除
    room.delete()
    return "success"


def add_inst_to_room(instpk, roompk):  # 使得某一个inst可以前往room
    inst = Instrument.objects.get(pk=instpk)
    if inst.room.filter(pk=roompk).count() >= 1:  # 如果该乐器已经可以前往该房间
        return "exist"
    room = Room.objects.get(pk=roompk)
    inst.room.add(room)
    return "success"


def remove_inst_from_room(instpk, roompk):  # 删除某一个inst可以前往room的关系
    inst = Instrument.objects.get(pk=instpk)
    if inst.room.filter(pk=roompk).count() == 0:  # 如果该乐器本来就不能前往该房间
        return "notexist"
    room = Room.objects.get(pk=roompk)
    inst.room.remove(room)
    return "success"


def remove_inst_from_all(instpk):  # 清理该乐器可以去的所有房间关系
    inst = Instrument.objects.get(pk=instpk)
    inst.room.clear()
    return "success"
