import json
from .models import *

DEFAULT_PRICE = -1

# * 乐器类型的价格管理


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
        raise ValueError("Two insttype prices conflict")


def set_type_price(usergrouppk, insttypepk, price):  # 更新价格
    tp = get_or_create_type_price(usergrouppk, insttypepk)
    tp.price = price
    tp.save()
    return tp.pk


def get_type_price(usergrouppk, insttypepk):
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


# * 房间价格的管理
def get_or_create_room_price(usergrouppk, roompk):  # 获取或创建一个room_price
    tp = RoomPrice.objects.filter(group__pk=usergrouppk, room__pk=roompk)
    if tp.count() == 1:
        return tp[0]
    elif tp.count() == 0:
        tppk = RoomPrice.objects.create_room_price(
            usergrouppk, roompk, DEFAULT_PRICE)
        return RoomPrice.objects.get(pk=tppk)
    else:
        raise ValueError("Two room prices conflict")


def set_room_price(usergrouppk, roompk, price):  # 更新价格
    tp = get_or_create_room_price(usergrouppk, roompk)
    tp.price = price
    tp.save()
    return tp.pk


def get_room_price(usergrouppk, roompk):
    tp = get_or_create_room_price(usergrouppk, roompk)
    return tp.price


def get_all_price_for_room(roompk):  # 获得所有用户组对该room的价格
    pricedata = []
    group_set = UserGroup.objects.all()
    for group in group_set:
        tp = get_or_create_room_price(
            group.pk, roompk)  # 获取所有当前room与group的pair
        priceinfo = {}
        priceinfo["grouppk"] = group.pk
        priceinfo["price"] = tp.price
        pricedata.append(priceinfo)
    json_data = json.dumps(pricedata, ensure_ascii=False)  # 转为json且避免乱码
    return json_data


def get_price(userpk, roompk, instpk):
    user = UserProfile.objects.get(pk=userpk)
    typepk = Instrument.objects.get(pk=instpk).type.pk

    roomprice = DEFAULT_PRICE
    typeprice = DEFAULT_PRICE

    for group in user.group.all():
        roomtp = get_or_create_room_price(group.pk, roompk)
        if roomtp.price != DEFAULT_PRICE:
            if roomprice == DEFAULT_PRICE:
                roomprice = roomtp.price
            else:
                roomprice = min(roomprice, roomtp.price)

        typetp = get_or_create_type_price(group.pk, typepk)
        if typetp.price != DEFAULT_PRICE:
            if typeprice == DEFAULT_PRICE:
                typeprice = typetp.price
            else:
                typeprice = min(typeprice, typetp.price)

    if roomprice == DEFAULT_PRICE or typeprice == DEFAULT_PRICE:
        return -1
    return roomprice + typeprice


def get_inst_price_user(userpk, instpk):
    user = UserProfile.objects.get(pk=userpk)
    typepk = Instrument.objects.get(pk=instpk).type.pk

    typeprice = DEFAULT_PRICE

    for group in user.group.all():
        typetp = get_or_create_type_price(group.pk, typepk)
        if typetp.price != DEFAULT_PRICE:
            if typeprice == DEFAULT_PRICE:
                typeprice = typetp.price
            else:
                typeprice = min(typeprice, typetp.price)

    if typeprice == DEFAULT_PRICE:
        return -1
    return typeprice
    '''
    totalprice = DEFAULT_PRICE
    for group in user.group.all():
        roomtp = get_or_create_room_price(group.pk, roompk)
        typetp = get_or_create_type_price(group.pk, typepk)
        if roomtp == DEFAULT_PRICE or typetp == DEFAULT_PRICE:
            continue
        if totalprice == DEFAULT_PRICE:
            totalprice = roomtp.price + typetp.price
        else:
            totalprice = min(totalprice, roomtp.price + typetp.price)
    if totalprice == DEFAULT_PRICE:
        return -1
    return totalprice
    '''
