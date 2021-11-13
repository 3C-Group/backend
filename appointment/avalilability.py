import json
from django.core import serializers
from .models import *
from django.db.models import Q
import datetime

TIME_FORMAT = '%Y/%m/%d %H:%M'


def check_room_order(roompk, begin, end):  # 检查时间段内是否有已经存在任何订单（unpaid & paid）
    result = get_room_order(roompk, begin, end)
    # 如果长度大于1，至少1个时间段无法获取. 或者长度为0，且它被禁用
    if len(result) > 1 or result[0]["type"] == "order":
        return True
    return False

# 获取所有该时段，对于roompk的各段order占用列表（不考虑禁用）


def get_room_order(roompk, begin, end) -> list:
    room = Room.objects.get(pk=roompk)
    timeset = set()
    order_set = Order.objects.filter(room__pk=roompk)
    order_set = order_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选出起始时间段到此刻的结束

    timeset.add(begin)
    timeset.add(end)

    for order in order_set.all():
        if order.begin_time >= begin and order.begin_time <= end:
            timeset.add(order.begin_time)
        if order.end_time >= begin and order.end_time <= end:
            timeset.add(order.end_time)
    timeset = sorted(timeset)

    stamplist = []
    for i in range(len(timeset) - 1):
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)
        ed = timeset[i+1]
        orders = order_set.filter(
            begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if orders.count() == room.max_inst:
            if orders.filter(status=Order.Status.PAID).count() > 0:
                stamplist.append(
                    {"time": ststr, "type": "order", "status": int(Order.Status.PAID)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "order", "status": int(Order.Status.UNPAID)})
        else:
            stamplist.append({"time": ststr, "type": "ok",  "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):
        if stamplist[i]["status"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result


def check_room_forbidden(userpk, roompk, begin, end):  # 检查时间段内是否该用户无法使用
    user = UserProfile.objects.get(pk=userpk)
    groupset = [group.pk for group in user.group.all()]
    result = get_room_rule(groupset, roompk, begin, end)
    # 如果长度大于1，至少1个时间段无法获取. 或者长度为0，且它被禁用
    if len(result) > 1 or result[0]["type"] == "forbidden":
        return True
    return False

# 获取所有该时段，对于usergrouppk_set以及roompk的各段时间列表（不考虑占用）


def get_room_rule(usergrouppk_set, roompk, begin, end) -> list:
    timeset = set()
    rule_set = ForbiddenRoom.objects.filter(room__pk=roompk)
    rule_set = rule_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选出起始时间段到此刻的结束
    rule_set = rule_set.filter(group__pk__in=usergrouppk_set)

    timeset.add(begin)
    timeset.add(end)
    for rule in rule_set.all():
        if rule.begin_time >= begin and rule.begin_time >= end:
            timeset.add(rule.begin_time)
        if rule.end_time >= begin and rule.end_time <= end:
            timeset.add(rule.end_time)
    timeset = sorted(timeset)

    stamplist = []
    for i in range(len(timeset) - 1):
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)
        ed = timeset[i+1]
        rules = rule_set.filter(begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if rules.count() == len(usergrouppk_set):
            if rules.filter(status=ForbiddenRoom.Status.FIX).count() > 0:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.FIX)})
            elif rules.filter(status=ForbiddenRoom.Status.ACTIVITY).count() > 0:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.ACTIVITY)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.OTHER)})
        else:
            stamplist.append({"time": ststr, "type": "ok",  "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # TODO: delete the last one
        if stamplist[i]["status"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result


def get_room_avaliability(userpk, roompk, begin_time, end_time):

    room = Room.objects.get(pk=roompk)

    begin = datetime.datetime.strptime(begin_time, TIME_FORMAT)
    end = datetime.datetime.strptime(end_time, TIME_FORMAT)
    user = UserProfile.objects.get(pk=userpk)
    usergrouppk_set = [group.pk for group in user.group.all()]

    rule_set = ForbiddenRoom.objects.filter(room__pk=roompk)
    rule_set = rule_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选出起始时间段到此刻的结束
    rule_set = rule_set.filter(group__pk__in=usergrouppk_set)

    order_set = Order.objects.filter(room__pk=roompk)  # 筛选房间
    order_set = order_set.filter(
        Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID))  # 筛选unpaid, paid
    order_set = order_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选时间   order_set = Order

    timeset = set()
    timeset.add(begin)
    timeset.add(end)
    for rule in rule_set.all():
        if rule.begin_time >= begin and rule.begin_time >= end:
            timeset.add(rule.begin_time)
        if rule.end_time >= begin and rule.end_time <= end:
            timeset.add(rule.end_time)
    for order in order_set.all():
        if order.begin_time >= begin and order.begin_time <= end:
            timeset.add(order.begin_time)
        if order.end_time >= begin and order.end_time <= end:
            timeset.add(order.end_time)
    timeset = sorted(timeset)

    stamplist = []
    for i in range(len(timeset) - 1):
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)
        ed = timeset[i+1]
        rules = rule_set.filter(begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if rules.count() == len(usergrouppk_set):  # 检查时间段是否被禁用
            if rules.filter(status=ForbiddenRoom.Status.FIX).count() > 0:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.FIX)})
            elif rules.filter(status=ForbiddenRoom.Status.ACTIVITY).count() > 0:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.ACTIVITY)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.OTHER)})
        else:  # 检查时间段是否存在订单
            orders = order_set.filter(begin_time__lte=st, end_time__gte=ed)
            if orders.count() == room.max_inst:  # 检查是否订单占满了房间
                if orders.filter(status=Order.Status.PAID).count() > 0:
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.PAID)})
                else:
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.UNPAID)})
            else:  # 没有订单 + 没有禁用
                stamplist.append({"time": ststr, "type": "ok", "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # TODO: delete the last one
        if stamplist[i]["type"] != stamplist[i-1]["type"] and stamplist[i]["status"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result
