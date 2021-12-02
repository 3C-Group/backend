import json
from django.core import serializers
from .models import *
from .availability import check_room_forbidden, check_room_order


def get_inst_type_info():  # 获取所有乐器类型的信息
    data = InstrumentType.objects.all()  # 返回dict格式的objects all

    typedata = [tp.get_dict() for tp in data]
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


def get_room_for_type(req):  # 获取某一类乐器的所有房间
    pk = req["typepk"]
    insts = InstrumentType.objects.get(
        pk=pk).instrument_set.all()  # 获取该类型乐器的所有乐器

    room_set = set()
    if "begin_time" in req and "end_time" in req:
        begin = datetime.datetime.strptime(req["begin_time"], TIME_FORMAT)
        end = datetime.datetime.strptime(req["end_time"], TIME_FORMAT)
        for inst in insts:
            for room in inst.room.all():
                if check_room_order(room.pk, begin, end):
                    continue
                if check_room_forbidden(req["userpk"], room.pk, begin, end):
                    continue
                room_set.add(room)
#            room_set = room_set.union(set(inst.room_set.all())  # 合并房间
    else:
        for inst in insts:
            room_set = room_set.union(inst.room.all())  # 合并房间

    retdata = {}
    retdata["roomnum"] = len(room_set)  # 统计数量
    retdata["data"] = [room.get_dict() for room in room_set]  # 房间的详情信息
    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data
