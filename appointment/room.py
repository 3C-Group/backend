import json
from django.core import serializers
from .models import *
from django.db.models import Q

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


def delete_room(pk):  # 删除某一房间
    room = Room.objects.get(pk=pk)  # 尝试获取该房间
    # 检查是否有1.即将支付，或者2.已支付但未使用的订单存在
    if room.order_set.filter(Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID)).count() != 0:
        return "order"  # 如果当前存在这样的房间，不能删除
    # TODO: 考虑该房间如果有乐器，这些乐器应该怎么删除
    room.delete()
    return "success"