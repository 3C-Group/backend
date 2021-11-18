import json
from django.core import serializers
from .models import *
from .avalilability import *
from django.db.models import Q
import datetime
from .instrument import remove_inst_from_room

TIME_FORMAT = '%Y/%m/%d %H:%M'


def get_room_info():  # 获取所有房间的信息
    data = serializers.serialize(
        "python", Room.objects.all())  # 返回dict格式的objects all

    roomdata = []
    for room in data:  # 统计数量，房间信息的详情信息
        roominfo = {}
        roominfo["pk"] = room["pk"]
        roominfo["name"] = room["fields"]["name"]
        roominfo["max_inst"] = room["fields"]["max_inst"]
        roominfo["inst"] = [inst.pk for inst in Room.objects.get(
            pk=room["pk"]).instrument_set.all()]  # 所有可到访的乐器
        roomdata.append(roominfo)

    retdata = {}
    retdata["roomnum"] = len(data)  # 统计数量
    retdata["data"] = roomdata  # 房间的详情信息

    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def delete_room(pk):  # 删除某一房间
    if(pk == 1):
        return "forbidden"
    room = Room.objects.get(pk=pk)  # 尝试获取该房间
    # 检查是否有1.即将支付，或者2.已支付但未使用的订单存在
    if room.order_set.filter(Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID)).count() != 0:
        return "order"  # 如果当前存在这样的房间，不能删除
    # TODO: 考虑该房间如果有乐器，这些乐器应该怎么删除
    for inst in room.inst.all():
        remove_inst_from_room(inst.pk, pk)
    room.delete()
    return "success"


def update_room(req):  # 修改房间信息
    room = Room.objects.get(pk=req["pk"])  # 获取该房间
    if "name" in req:
        room.name = req["name"]
    if "max_inst" in req:
        room.max_inst = req["max_inst"]
    room.save()
    return "success"


def check_rule(usergrouppk, roompk, begin, end):  # 检查这一时间段, 对于该room和usergroup, 是否有重合的禁用规则
    rule_set = ForbiddenRoom.objects.filter(
        group__pk=usergrouppk, room__pk=roompk)
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的order, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的order, 满足结束时间大于begin
    rule_set = rule_set.filter(qbegin & qend)  # 筛选和该时间段重合的rule
    if rule_set.count() > 1:
        return True
    return False


def check_order(usergrouppk, roompk, begin, end):  # 检查这一时间段，是否有关于该room, 与该usergroup相关的订单
    usergroup = UserGroup.objects.get(pk=usergrouppk)
    order_set = Order.objects.filter(room__pk=roompk)  # 筛选房间
    order_set = order_set.filter(
        Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID))  # 筛选unpaid, paid
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的order, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的order, 满足结束时间大于begin
    order_set = order_set.filter(qbegin & qend)  # 筛选时间
    # 存在包括该usergroup的order
    if order_set.filter(user__in=usergroup.userprofile_set.all()).count() > 0:
        return True
    return False


def set_room_forbidden(req):  # 设置房间禁用  [begin_time, end_time)
    begin_time = datetime.datetime.strptime(req["begin_time"], TIME_FORMAT)
    end_time = datetime.datetime.strptime(req["end_time"], TIME_FORMAT)
    if end_time <= begin_time:
        raise ValueError("time length error")  # 时间长度错误

    if check_rule(req["usergrouppk"], req["roompk"], begin_time, end_time):  # 检查是否有已重合的规则
        return "already forbidden"

    # 检查是否有相关group与room的订单(unpaid and paid)
    if check_order(req["usergrouppk"], req["roompk"], begin_time, end_time):
        return "order conflict"

    if req["status"] == 1:  # 设置禁用的理由
        status = ForbiddenRoom.Status.FIX
    elif req["status"] == 2:
        status = ForbiddenRoom.Status.ACTIVITY
    else:
        status = ForbiddenRoom.Status.OTHER

    rulepk = ForbiddenRoom.objects.create_rule(
        req["usergrouppk"], req["roompk"], begin_time, end_time, status)
    return rulepk
