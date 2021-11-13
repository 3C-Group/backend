import json
from django.core import serializers
from .models import *
from .price import get_price
from .avalilability import *

TIME_FORMAT = '%Y/%m/%d %H:%M'


def get_order(req):
    data = serializers.serialize("json", Order.objects.all())
    return data


def create_order(req):
    begin_time = datetime.datetime.strptime(req["begin_time"], TIME_FORMAT)
    end_time = datetime.datetime.strptime(req["end_time"], TIME_FORMAT)
    if end_time <= begin_time:
        raise ValueError("time length too short")

    if check_room_forbidden(req["userpk"], req["roompk"], begin_time, end_time):
        return "room forbidden"

    if check_room_order(req["roompk"], begin_time, end_time):
        return "order conflict"

    # TODO: check inst

    price = get_price(req["userpk"], req["roompk"], req["instpk"])

    # TODO : paid在支付时才计算

    orderpk = Order.objects.create_order(
        req["userpk"], req["roompk"], req["instpk"], price, begin_time, end_time)
    return orderpk
