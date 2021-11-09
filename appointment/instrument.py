import json
from django.core import serializers
from .models import *
from django.db.models import Q

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

def delete_inst(pk):  # 删除某一乐器
    inst = Instrument.objects.get(pk=pk)  # 尝试获取该乐器
    # 检查是否有1.即将支付，或者2.已支付但未使用的订单存在
    if inst.order_set.filter(Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID)).count() != 0:
        return "order"  # 如果当前存在这样的乐器，不能删除
    inst.delete()
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

#    if inst.room.filter(pk=roompk).count() == 0:  # 如果该乐器本来就不能前往该房间
#        return "notexist"
#    TODO: not working here
#    if Order.objects.all().filter(room=roompk,inst=instpk).count() == 0:  #存在对应的订单
#        return "related order exist"
    # TODO
    room = Room.objects.get(pk=roompk)
    inst.room.remove(room)
    return "success"
