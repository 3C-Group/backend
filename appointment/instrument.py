import json
from django.core import serializers
from .models import *
from django.db.models import Q


def get_inst_info():  # 获取所有乐器的信息
    data = Instrument.objects.all()  # 返回dict格式的objects all
    instdata = [inst.get_dict() for inst in data]
    retdata = {}
    retdata["instnum"] = len(data)  # 统计数量
    retdata["data"] = instdata  # 乐器的详情信息
    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def get_inst_for_type(pk):
    data = Instrument.objects.filter(type__pk=pk)
    instdata = [inst.get_dict() for inst in data]
    retdata = {}
    retdata["instnum"] = len(data)  # 统计数量
    retdata["data"] = instdata  # 乐器的详情信息
    json_data = json.dumps(retdata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def delete_inst(pk):  # 删除某一乐器
    if(pk == 1):
        return "forbidden"
    inst = Instrument.objects.get(pk=pk)  # 尝试获取该乐器
    # 检查是否有1.即将支付，或者2.已支付但未使用的订单存在
    if inst.order_set.filter(Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID)).count() != 0:
        return "order"  # 如果当前存在这样的乐器，不能删除
    inst.delete()
    return "success"


def update_inst(req):
    pk = req["pk"]
    if pk == 1:
        return "forbidden"
    inst = Instrument.objects.get(pk=req["pk"])  # 尝试获取该乐器
    if "name" in req:
        inst.name = req["name"]
    inst.save()
    return "success"


def check_inst_in_room(instpk, roompk):  # 检查该乐器是否可以前往该房间
    return Instrument.objects.get(pk=instpk).room.filter(pk=roompk).count() >= 1


def add_inst_to_room(instpk, roompk):  # 使得某一个inst可以前往room
    inst = Instrument.objects.get(pk=instpk)
    if check_inst_in_room(instpk, roompk):  # 如果该乐器已经可以前往该房间
        return "exist"
    room = Room.objects.get(pk=roompk)
    inst.room.add(room)
    return "success"


def remove_inst_from_room(instpk, roompk):  # 删除某一个inst可以前往room的关系
    inst = Instrument.objects.get(pk=instpk)
    if not check_inst_in_room(instpk, roompk):  # 如果该乐器本来就不能前往该房间
        return "notexist"
#    if Order.objects.all().filter(room=roompk,inst=instpk).count() == 0:  #存在对应的订单
#        return "related order exist"
    # TODO
    room = Room.objects.get(pk=roompk)
    inst.room.remove(room)
    return "success"


def check_rule(usergrouppk, instpk, begin, end):  # 检查这一时间段, 对于该inst和usergroup, 是否有重合的禁用规则
    rule_set = ForbiddenInstrument.objects.filter(
        group__pk=usergrouppk, inst__pk=instpk)
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的order, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的order, 满足结束时间大于begin
    rule_set = rule_set.filter(qbegin & qend)  # 筛选和该时间段重合的rule
    if rule_set.count() > 1:
        return True
    return False


def check_order(usergrouppk, instpk, begin, end):  # 检查这一时间段，是否有关于该inst, 与该usergroup相关的订单
    usergroup = UserGroup.objects.get(pk=usergrouppk)
    order_set = Order.objects.filter(inst__pk=instpk)  # 筛选乐器
    order_set = order_set.filter(
        Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID))  # 筛选unpaid, paid
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的order, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的order, 满足结束时间大于begin
    order_set = order_set.filter(qbegin & qend)  # 筛选时间
    # 存在包括该usergroup的order
    if order_set.filter(user__in=usergroup.userprofile_set.all()).count() > 0:
        return True
    return False


def set_inst_forbidden(req):  # 设置乐器禁用  [begin_time, end_time)
    if req["instpk"] == 1:
        return "forbidden"
    begin_time = datetime.datetime.strptime(req["begin_time"], TIME_FORMAT)
    end_time = datetime.datetime.strptime(req["end_time"], TIME_FORMAT)
    if end_time <= begin_time:
        raise ValueError("time length error")  # 时间长度错误

    if check_rule(req["usergrouppk"], req["instpk"], begin_time, end_time):  # 检查是否有已重合的规则
        return "already forbidden"

    # 检查是否有相关group与inst的订单(unpaid and paid)
    if check_order(req["usergrouppk"], req["instpk"], begin_time, end_time):
        return "order conflict"

    if req["status"] == 1:  # 设置禁用的理由
        status = ForbiddenInstrument.Status.FIX
    elif req["status"] == 2:
        status = ForbiddenInstrument.Status.ACTIVITY
    else:
        status = ForbiddenInstrument.Status.OTHER

    rulepk = ForbiddenInstrument.objects.create_rule(
        req["usergrouppk"], req["instpk"], begin_time, end_time, status)
    return rulepk
