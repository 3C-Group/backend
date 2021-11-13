import json
from django.core import serializers
from .models import *
from django.db.models import Q
import datetime

TIME_FORMAT = '%Y/%m/%d %H:%M'


def check_room_forbidden(userpk, roompk, begin, end):  # 检查时间段内是否该用户无法使用
    user = UserProfile.objects.get(pk=userpk)
    groupset = [group.pk for group in user.group.all()]
    result = get_room_rule(groupset, roompk, begin, end)
    if len(result) > 1:  # 如果长度大于1， 至少1个时间段无法获取
        return True
    return False


def check_room_order(roompk, begin, end):  # 检查时间段内是否有已经存在订单（unpaid & paid）
    order_set = Order.objects.filter(room__pk=roompk)  # 筛选房间
    order_set = order_set.filter(
        Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID))  # 筛选unpaid, paid
    order_set = order_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选时间
    if order_set.count() > 0:
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
        timeset.add(rule.begin_time)
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
        timeset.add(rule.begin_time)
        timeset.add(rule.end_time)
    for order in order_set.all():
        timeset.add(order.begin_time)
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
            if orders.count() > 0:  # 检查是否存在订单
                if orders.filter(status=Order.Status.UNPAID).count() > 0:
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.UNPAID)})
                else:
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.PAID)})
            else:  # 没有订单 + 没有禁用
                stamplist.append({"time": ststr, "type": "ok", "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # TODO: delete the last one
        if stamplist[i]["type"] != stamplist[i-1]["type"] and stamplist[i]["status"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result
