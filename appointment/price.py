import json
from django.core import serializers
from .models import *


DEFAULT_PRICE = 9999999


def get_or_create_type_price(usergrouppk, insttypepk):  # 获取或创建一个type_price
    tp = InstrumentTypePrice.objects.filter(
        group__pk=usergrouppk, insttype__pk=insttypepk)
    if tp.count() == 1:
        return tp[0]
    elif tp.count() == 0:
        tppk = InstrumentTypePrice.objects.create_type_price(
            usergrouppk, insttypepk, DEFAULT_PRICE)
        return InstrumentTypePrice.objects.get(pk=tppk)
    else:
        raise ValueError("Two type price conflict")


def set_type_price(usergrouppk, insttypepk, price):  # 更新价格
    tp = get_or_create_type_price(usergrouppk, insttypepk)
    tp.price = price
    tp.save()
    return tp.pk


def get_type_price(usergrouppk, insttypepk, price):
    tp = get_or_create_type_price(usergrouppk, insttypepk)
    return tp.price


def get_all_price_for_type(insttypepk):  # 获得所有用户组对该乐器类型的价格
    pricedata = []
    group_set = UserGroup.objects.all()
    for group in group_set:
        # 获取所有当前insttype与group的pair
        tp = get_or_create_type_price(group.pk, insttypepk)
        priceinfo = {}
        priceinfo["grouppk"] = group.pk
        priceinfo["price"] = tp.price
        pricedata.append(priceinfo)
    json_data = json.dumps(pricedata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data
