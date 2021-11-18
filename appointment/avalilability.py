import json
from django.core import serializers
from .models import *
from django.db.models import Q
import datetime

TIME_FORMAT = '%Y/%m/%d %H:%M'


def check_room_order(roompk, begin, end):  # 检查时间段内，订单有关的占用情况
    result = get_room_order(roompk, begin, end)
    # 如果长度大于1，至少1个时间段无法获取. 或者长度为0，且它是一个order
    if len(result) > 1 or result[0]["type"] == "order":
        return True
    return False

# 获取所有该时段，对于roompk的各段order占用列表（不考虑禁用）
# 当order(paid and unpaid)数量达到room的max_inst时，room才被占用


def get_room_order(roompk, begin, end) -> list:
    order_set = Order.objects.filter(room__pk=roompk)  # 筛选与该room有关order
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的order, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的order, 满足结束时间大于begin
    order_set = order_set.filter(qbegin & qend)

    timeset = set()
    timeset.add(begin)
    timeset.add(end)

    for order in order_set.all():  # 收集范围内，所有涉及到的时间戳
        if order.begin_time >= begin and order.begin_time <= end:
            timeset.add(order.begin_time)
        if order.end_time >= begin and order.end_time <= end:
            timeset.add(order.end_time)
    timeset = sorted(timeset)

    room = Room.objects.get(pk=roompk)

    stamplist = []
    for i in range(len(timeset) - 1):  # 对于时间戳的每一个间隔，进行处理
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)  # 格式化输出
        ed = timeset[i+1]
        orders = order_set.filter(
            begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if orders.count() == room.max_inst:  # 当订单数量达到max_inst
            if orders.filter(status=Order.Status.PAID).count() > 0:  # 优先展示已支付的订单
                stamplist.append(
                    {"time": ststr, "type": "order", "status": int(Order.Status.PAID)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "order", "status": int(Order.Status.UNPAID)})
        else:
            stamplist.append({"time": ststr, "type": "ok",  "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # 合并所有冗余的时间段
        if stamplist[i]["status"] != stamplist[i-1]["status"] and stamplist[i]["type"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result


def check_room_forbidden(userpk, roompk, begin, end):  # 检查时间段内是否该用户无法使用
    user = UserProfile.objects.get(pk=userpk)
    groupset = [group.pk for group in user.group.all()]  # 搜集用户的所有用户组标签
    result = get_room_rule(groupset, roompk, begin, end)
    # 如果长度大于1，至少1个时间段无法获取. 或者长度为0，且它被禁用
    if len(result) > 1 or result[0]["type"] == "forbidden":
        return True
    return False

# 获取所有该时段，对于usergrouppk_set以及roompk的各段时间列表（不考虑占用）


def get_room_rule(usergrouppk_set, roompk, begin, end) -> list:
    rule_set = ForbiddenRoom.objects.filter(room__pk=roompk)
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的rule, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的rule, 满足结束时间大于begin
    rule_set = rule_set.filter(qbegin & qend)
    rule_set = rule_set.filter(group__pk__in=usergrouppk_set)
    # 筛选出与该用户组，房间以及时间段重叠的禁用规则

    timeset = set()  # 搜集所有相关的时间戳
    timeset.add(begin)
    timeset.add(end)
    for rule in rule_set.all():
        if rule.begin_time >= begin and rule.begin_time >= end:
            timeset.add(rule.begin_time)
        if rule.end_time >= begin and rule.end_time <= end:
            timeset.add(rule.end_time)
    timeset = sorted(timeset)

    stamplist = []
    for i in range(len(timeset) - 1):  # 对于每个时间段，进行判断
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)  # 格式化输出
        ed = timeset[i+1]
        rules = rule_set.filter(
            begin_time__lte=st, end_time__gte=ed)  # 筛选所有该时间段的规则
        if rules.count() == len(usergrouppk_set):  # 该用户的所有group都对这个规则禁用
            if rules.filter(status=ForbiddenRoom.Status.FIX).count() > 0:  # 优先展示原因：维修中
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.FIX)})
            elif rules.filter(status=ForbiddenRoom.Status.ACTIVITY).count() > 0:  # 活动占用
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.ACTIVITY)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.OTHER)})
        else:
            stamplist.append({"time": ststr, "type": "ok",  "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # 删除冗余的部分
        if stamplist[i]["status"] != stamplist[i-1]["status"] and stamplist[i]["type"] != stamplist[i-1]["type"]:
            result.append(stamplist[i])

    return result


# 给定user, room, 以及时间段，返回这一整段时间内，room的可用性
def get_room_avaliability(userpk, roompk, begin_time, end_time):

    # 计算时间
    begin = datetime.datetime.strptime(begin_time, TIME_FORMAT)
    end = datetime.datetime.strptime(end_time, TIME_FORMAT)

    # 搜集用户的所有用户组标签
    user = UserProfile.objects.get(pk=userpk)
    usergrouppk_set = [group.pk for group in user.group.all()]

    # 搜集相关禁用规则
    rule_set = ForbiddenRoom.objects.filter(room__pk=roompk)
    rule_set = rule_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选出起始时间段到此刻的结束
    rule_set = rule_set.filter(group__pk__in=usergrouppk_set)

    # 搜集相关订单
    order_set = Order.objects.filter(room__pk=roompk)  # 筛选房间
    order_set = order_set.filter(
        Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID))  # 筛选unpaid, paid
    order_set = order_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选时间   order_set = Order

    timeset = set()  # 搜集时间戳
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

    room = Room.objects.get(pk=roompk)
    stamplist = []
    for i in range(len(timeset) - 1):  # 对每个时间戳进行判断
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)
        ed = timeset[i+1]
        rules = rule_set.filter(begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if rules.count() == len(usergrouppk_set):  # 检查时间段是否被禁用, 优先展示被禁用的情况
            if rules.filter(status=ForbiddenRoom.Status.FIX).count() > 0:  # 优先展示维修中
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.FIX)})
            elif rules.filter(status=ForbiddenRoom.Status.ACTIVITY).count() > 0:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.ACTIVITY)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenRoom.Status.OTHER)})
        else:  # 检查时间段是否存在订单。 如果它没有被禁用，才试图展示这个时间段存在订单
            orders = order_set.filter(begin_time__lte=st, end_time__gte=ed)
            if orders.count() == room.max_inst:  # 检查是否订单占满了房间
                if orders.filter(status=Order.Status.PAID).count() > 0:  # 优先展示已支付
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.PAID)})
                else:
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.UNPAID)})
            else:  # 没有订单 + 没有禁用
                stamplist.append({"time": ststr, "type": "ok", "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # 删除冗余信息
        if stamplist[i]["type"] != stamplist[i-1]["type"] and stamplist[i]["status"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result


def check_inst_order(instpk, begin, end):  # 检查时间段内，订单有关的占用情况
    result = get_inst_order(instpk, begin, end)
    # 如果长度大于1，至少1个时间段无法获取. 或者长度为0，且它是一个order
    if len(result) > 1 or result[0]["type"] == "order":
        return True
    return False

# 获取所有该时段，对于instpk的各段order占用列表（不考虑禁用）


def get_inst_order(instpk, begin, end) -> list:
    order_set = Order.objects.filter(inst__pk=instpk)  # 筛选与该inst有关order
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的order, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的order, 满足结束时间大于begin
    order_set = order_set.filter(qbegin & qend)

    timeset = set()
    timeset.add(begin)
    timeset.add(end)

    for order in order_set.all():  # 收集范围内，所有涉及到的时间戳
        if order.begin_time >= begin and order.begin_time <= end:
            timeset.add(order.begin_time)
        if order.end_time >= begin and order.end_time <= end:
            timeset.add(order.end_time)
    timeset = sorted(timeset)

    inst = Instrument.objects.get(pk=instpk)

    stamplist = []
    for i in range(len(timeset) - 1):  # 对于时间戳的每一个间隔，进行处理
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)  # 格式化输出
        ed = timeset[i+1]
        orders = order_set.filter(
            begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if orders.count() == 1:  # 如果有订单
            if orders.filter(status=Order.Status.PAID).count() > 0:  # 优先展示已支付的订单
                stamplist.append(
                    {"time": ststr, "type": "order", "status": int(Order.Status.PAID)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "order", "status": int(Order.Status.UNPAID)})
        else:
            stamplist.append({"time": ststr, "type": "ok",  "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # 合并所有冗余的时间段
        if stamplist[i]["status"] != stamplist[i-1]["status"] and stamplist[i]["type"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result


def check_inst_forbidden(userpk, instpk, begin, end):  # 检查时间段内是否该用户无法使用
    user = UserProfile.objects.get(pk=userpk)
    groupset = [group.pk for group in user.group.all()]  # 搜集用户的所有用户组标签
    result = get_inst_rule(groupset, instpk, begin, end)
    # 如果长度大于1，至少1个时间段无法获取. 或者长度为0，且它被禁用
    if len(result) > 1 or result[0]["type"] == "forbidden":
        return True
    return False

# 获取所有该时段，对于usergrouppk_set以及instpk的各段时间列表（不考虑占用）


def get_inst_rule(usergrouppk_set, instpk, begin, end) -> list:
    rule_set = ForbiddenInstrument.objects.filter(inst__pk=instpk)
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的rule, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的rule, 满足结束时间大于begin
    rule_set = rule_set.filter(qbegin & qend)
    rule_set = rule_set.filter(group__pk__in=usergrouppk_set)
    # 筛选出与该用户组，乐器以及时间段重叠的禁用规则

    timeset = set()  # 搜集所有相关的时间戳
    timeset.add(begin)
    timeset.add(end)
    for rule in rule_set.all():
        if rule.begin_time >= begin and rule.begin_time >= end:
            timeset.add(rule.begin_time)
        if rule.end_time >= begin and rule.end_time <= end:
            timeset.add(rule.end_time)
    timeset = sorted(timeset)

    stamplist = []
    for i in range(len(timeset) - 1):  # 对于每个时间段，进行判断
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)  # 格式化输出
        ed = timeset[i+1]
        rules = rule_set.filter(
            begin_time__lte=st, end_time__gte=ed)  # 筛选所有该时间段的规则
        if rules.count() == len(usergrouppk_set):  # 该用户的所有group都对这个规则禁用
            if rules.filter(status=ForbiddenInstrument.Status.FIX).count() > 0:  # 优先展示原因：维修中
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenInstrument.Status.FIX)})
            elif rules.filter(status=ForbiddenInstrument.Status.ACTIVITY).count() > 0:  # 活动占用
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenInstrument.Status.ACTIVITY)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenInstrument.Status.OTHER)})
        else:
            stamplist.append({"time": ststr, "type": "ok",  "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # 删除冗余的部分
        if stamplist[i]["status"] != stamplist[i-1]["status"] and stamplist[i]["type"] != stamplist[i-1]["type"]:
            result.append(stamplist[i])

    return result


# 给定user, inst, 以及时间段，返回这一整段时间内，inst的可用性
def get_inst_avaliability(userpk, instpk, begin_time, end_time):

    # 计算时间
    begin = datetime.datetime.strptime(begin_time, TIME_FORMAT)
    end = datetime.datetime.strptime(end_time, TIME_FORMAT)

    # 搜集用户的所有用户组标签
    user = UserProfile.objects.get(pk=userpk)
    usergrouppk_set = [group.pk for group in user.group.all()]

    # 搜集相关禁用规则
    rule_set = ForbiddenInstrument.objects.filter(inst__pk=instpk)
    rule_set = rule_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选出起始时间段到此刻的结束
    rule_set = rule_set.filter(group__pk__in=usergrouppk_set)

    # 搜集相关订单
    order_set = Order.objects.filter(inst__pk=instpk)  # 筛选乐器
    order_set = order_set.filter(
        Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID))  # 筛选unpaid, paid
    order_set = order_set.filter(Q(begin_time__range=(
        begin, end - datetime.timedelta(minutes=1))) | Q(end_time__range=(begin + datetime.timedelta(minutes=1), end)))  # 筛选时间   order_set = Order

    timeset = set()  # 搜集时间戳
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

    inst = Instrument.objects.get(pk=instpk)
    stamplist = []
    for i in range(len(timeset) - 1):  # 对每个时间戳进行判断
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)
        ed = timeset[i+1]
        rules = rule_set.filter(begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if rules.count() == len(usergrouppk_set):  # 检查时间段是否被禁用, 优先展示被禁用的情况
            if rules.filter(status=ForbiddenInstrument.Status.FIX).count() > 0:  # 优先展示维修中
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenInstrument.Status.FIX)})
            elif rules.filter(status=ForbiddenInstrument.Status.ACTIVITY).count() > 0:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenInstrument.Status.ACTIVITY)})
            else:
                stamplist.append(
                    {"time": ststr, "type": "forbidden", "status": int(ForbiddenInstrument.Status.OTHER)})
        else:  # 检查时间段是否存在订单。 如果它没有被禁用，才试图展示这个时间段存在订单
            orders = order_set.filter(begin_time__lte=st, end_time__gte=ed)
            if orders.count() == 1:  # 如果有订单
                if orders.filter(status=Order.Status.PAID).count() > 0:  # 优先展示已支付
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.PAID)})
                else:
                    stamplist.append(
                        {"time": ststr, "type": "order", "status": int(Order.Status.UNPAID)})
            else:  # 没有订单 + 没有禁用
                stamplist.append({"time": ststr, "type": "ok", "status": 0})

    result = []
    result.append(stamplist[0])
    for i in range(1, len(timeset) - 1):  # 删除冗余信息
        if stamplist[i]["type"] != stamplist[i-1]["type"] and stamplist[i]["status"] != stamplist[i-1]["status"]:
            result.append(stamplist[i])

    return result
