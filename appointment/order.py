import json
from django.core import serializers
from .models import *
from .price import get_price
from .avalilability import *

TIME_FORMAT = '%Y/%m/%d %H:%M'  # 时间格式


def get_order(req):  # TODO
    data = serializers.serialize("json", Order.objects.all())
    return data


def create_order(req):  # 给定时间段， 房间， 乐器，用户： 创建一个订单
    begin_time = datetime.datetime.strptime(req["begin_time"], TIME_FORMAT)
    end_time = datetime.datetime.strptime(req["end_time"], TIME_FORMAT)
    if end_time <= begin_time:
        raise ValueError("invalid time length")

    # TODO: 检查乐器的占用与禁用
    # check_inst_forbidden
    # check_inst_order

    if check_room_forbidden(req["userpk"], req["roompk"], begin_time, end_time):
        return "room forbidden"

    if check_room_order(req["roompk"], begin_time, end_time):
        return "room order conflict"

    price = get_price(req["userpk"], req["roompk"], req["instpk"])

    orderpk = Order.objects.create_order(
        req["userpk"], req["roompk"], req["instpk"], price, begin_time, end_time)
    return orderpk
