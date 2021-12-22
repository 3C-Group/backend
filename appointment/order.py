import json
from functools import reduce
from django.core import serializers
from .models import *
from .price import get_price
from .availability import *
from .instrument import check_inst_in_room
from math import ceil

TIME_FORMAT = '%Y/%m/%d %H:%M'  # 时间格式

status_dict = {"PAID": Order.Status.UNPAID, "FINISHED": Order.Status.FINISHED,
               "CANCELLED": Order.Status.CANCELLED, "UNPAID": Order.Status.UNPAID, "OUTDATED": Order.Status.OUTDATED}


def get_order(req):  # TODO
    Qset = set()
    if "orderpk" in req:
        Qset.add(Q(pk=req["orderpk"]))
    else:
        if "userpk" in req:
            Qset.add(Q(user_id=req["userpk"]))
        if "roompk" in req:
            Qset.add(Q(room_id=req["roompk"]))
        if "instpk" in req:
            Qset.add(Q(inst_id=req["instpk"]))
        if "begin_time" in req:
            begin_time = datetime.datetime.strptime(
                req["begin_time"], TIME_FORMAT)
            Qset.add(Q(begin_time__gte=begin_time))
        if "end_time" in req:
            end_time = datetime.datetime.strptime(req["end_time"], TIME_FORMAT)
            Qset.add(Q(end_time__lte=end_time))
        if "status" in req:
            Qset.add(Q(status=status_dict[req["status"]]))
        if "hash" in req:
            Qset.add(Q(hash__startswith=req["hash"]))
    if len(Qset) == 0:
        return "empty Qset"
    data = Order.objects.filter(reduce(lambda x, y: x & y, Qset))
    if len(data) == 0:
        return "not found"
    if "begin_num" in req and "end_num" in req:
        data = data.order_by(
            "-begin_time")[int(req["begin_num"]):int(req["end_num"])]
    ret_data = [item.get_dict() for item in data]  # 格式化
    ret_data.append(len(data))
    json_data = json.dumps(ret_data, ensure_ascii=False)
    return json_data


def get_all_order(req):  # for test only
    data = serializers.serialize("json", Order.objects.all())
    return data


def create_order(req):  # 给定时间段， 房间， 乐器，用户： 创建一个订单
    begin_time = datetime.datetime.strptime(req["begin_time"], TIME_FORMAT)
    if begin_time <= datetime.datetime.now() + datetime.timedelta(hours=1):
        return "begin time is in the past"
    if begin_time.date() > datetime.datetime.now().date() + datetime.timedelta(days=7):
        return "begin time is too far away"
    end_time = datetime.datetime.strptime(req["end_time"], TIME_FORMAT)
    if end_time <= begin_time:
        raise ValueError("invalid time length")
    if end_time.date() > begin_time.date():
        return "end time must in the same day"
    if end_time > begin_time + datetime.timedelta(hours=3):
        return "too long period"

    price = ceil(get_price(req["userpk"], req["roompk"], req["instpk"]) * \
        ((float((end_time.date() - begin_time.date()).seconds)) / 3600))
    if price == -1:
        return "no permission to use"

    if not check_inst_in_room(req["instpk"], req["roompk"]):
        return "inst not in the room"

    if check_inst_forbidden(req["userpk"], req["instpk"], begin_time, end_time):
        return "inst forbidden"

    if check_inst_order(req["instpk"], begin_time, end_time):
        return "inst order conflict"

    if check_room_forbidden(req["userpk"], req["roompk"], begin_time, end_time):
        return "room forbidden"

    if check_room_order(req["roompk"], begin_time, end_time):
        return "room order conflict"

    orderpk = Order.objects.create_order(
        req["userpk"], req["roompk"], req["instpk"], price, begin_time, end_time)
    return orderpk


def get_order_in_range(begin, end):
    order_set = Order.objects.order_by('-begin_time')[int(begin): int(end)]
    order_data = [order.get_dict() for order in order_set]
    json_data = json.dumps(order_data, ensure_ascii=False)
    return json_data


def verify_order(order_token):
    order = Order.objects.get(hash=order_token)
    if order.status == Order.STATUS_PAID:
        order.status = Order.STATUS_FINISHED
        order.save()
        return True
    return False
