from django.core import serializers
from .models import *
from django.db.models import Q
from .price import get_type_price, get_room_price
import datetime


def check_room_order(roompk, begin, end):  # 检查时间段内，订单有关的占用情况
    if roompk == 1:
        return False
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
    if roompk == 1:
        return False
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
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的rule, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的rule, 满足结束时间大于begin
    rule_set = rule_set.filter(qbegin & qend)
    rule_set = rule_set.filter(group__pk__in=usergrouppk_set)

    # 搜集相关订单
    order_set = Order.objects.filter(room__pk=roompk)  # 筛选房间
    order_set = order_set.filter(
        Q(status=Order.Status.UNPAID) | Q(status=Order.Status.PAID))  # 筛选unpaid, paid
    order_set = order_set.filter(qbegin & qend)

    timeset = set()  # 搜集时间戳
    timeset.add(begin)
    timeset.add(end)
    for rule in rule_set.all():
        if rule.begin_time >= begin and rule.begin_time <= end:
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
        if rules.count() >= len(usergrouppk_set):  # 检查时间段是否被禁用, 优先展示被禁用的情况
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
    if instpk == 1:
        return False
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
    if instpk == 1:
        return False
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
        if rule.begin_time >= begin and rule.begin_time <= end:
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
    stamplist = []
    if instpk == 1:
        ststr = datetime.datetime.strftime(begin_time, TIME_FORMAT)
        stamplist.append({"time": ststr, "type": "ok", "status": 0})
        return stamplist

    # 计算时间
    begin = datetime.datetime.strptime(begin_time, TIME_FORMAT)
    end = datetime.datetime.strptime(end_time, TIME_FORMAT)

    # 搜集用户的所有用户组标签
    user = UserProfile.objects.get(pk=userpk)
    usergrouppk_set = [group.pk for group in user.group.all()]

    # 搜集相关禁用规则
    rule_set = ForbiddenInstrument.objects.filter(inst__pk=instpk)
    qbegin = Q(begin_time__lt=end)  # 涉及到该时间段(begin, end)的rule, 满足开始时间小于end
    qend = Q(end_time__gt=begin)  # 涉及到该时间段(begin, end)的rule, 满足结束时间大于begin
    rule_set = rule_set.filter(qbegin & qend)
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
        if rule.begin_time >= begin and rule.begin_time <= end:
            timeset.add(rule.begin_time)
        if rule.end_time >= begin and rule.end_time <= end:
            timeset.add(rule.end_time)
    for order in order_set.all():
        if order.begin_time >= begin and order.begin_time <= end:
            timeset.add(order.begin_time)
        if order.end_time >= begin and order.end_time <= end:
            timeset.add(order.end_time)
    timeset = sorted(timeset)

    for i in range(len(timeset) - 1):  # 对每个时间戳进行判断
        st = timeset[i]
        ststr = datetime.datetime.strftime(st, TIME_FORMAT)
        ed = timeset[i+1]
        rules = rule_set.filter(begin_time__lte=st, end_time__gte=ed)  # 筛选时间段
        if rules.count() >= len(usergrouppk_set):  # 检查时间段是否被禁用, 优先展示被禁用的情况
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


def get_room_avalist(userpk, roompk, begin_time, end_time):
    # 搜集用户的所有用户组标签
    user = UserProfile.objects.get(pk=userpk)
    usergrouppk_set = [group.pk for group in user.group.all()]

    flag = False
    for grouppk in usergrouppk_set:
        if get_room_price(grouppk, roompk) != -1:
            flag = True
            break
    if not flag:
        return []
    return get_room_avaliability(userpk, roompk, begin_time, end_time)


def get_inst_avalist(userpk, typepk, begin_time, end_time):
    # 计算时间
    begin = datetime.datetime.strptime(begin_time, TIME_FORMAT)
    end = datetime.datetime.strptime(end_time, TIME_FORMAT)

    # 搜集用户的所有用户组标签
    user = UserProfile.objects.get(pk=userpk)
    usergrouppk_set = [group.pk for group in user.group.all()]

    aval = []
    unaval = []

    insts = Instrument.objects.filter(type__pk=typepk)
    flag = False
    for grouppk in usergrouppk_set:
        if get_type_price(grouppk, typepk) != -1:
            flag = True
            break
    if not flag:
        for inst in insts:
            unaval.append({"pk": inst.pk, "name": inst.name})
        return aval, unaval
    for inst in insts:
        instaval = get_inst_avaliability(userpk, inst.pk, begin_time, end_time)
        inst_ava = []
        for i in range(len(instaval)):
            if instaval[i]["type"] == "ok":
                inst_ava.append((datetime.datetime.strptime(instaval[i]["time"], TIME_FORMAT), end if i+1 == len(instaval)
                                else datetime.datetime.strptime(instaval[i+1]["time"], TIME_FORMAT)))
        begin_set = set()
        end_set = set()
        instpk = inst.pk
        instroom_set = inst.room.all()
        for room in instroom_set:
            roompk = room.pk
            roomaval = get_room_avalist(userpk, roompk, begin_time, end_time)
            for i in range(len(roomaval)):
                if roomaval[i]["type"] == "ok":
                    begin_set.add(datetime.datetime.strptime(
                        roomaval[i]["time"], TIME_FORMAT))
                    end_set.add(end if i+1 == len(roomaval)
                                else datetime.datetime.strptime(roomaval[i+1]["time"], TIME_FORMAT))
        if len(begin_set) == 0:
            unaval.append({"pk": instpk, "name": inst.name})
            continue
        begin_set = sorted(begin_set)
        end_set = sorted(end_set)
        time_list = []
        result = []
        j = 1
        cur_time = begin_set[0]
        while j < len(end_set):
            if begin_set[j] <= end_set[j-1]:
                ++j
            else:
                time_list.append((cur_time, end_set[j-1]))
                cur_time = begin_set[j]
                ++j
        time_list.append((cur_time, end_set[j-1]))
        for inst_ava_duration in inst_ava:
            time_begin = inst_ava_duration[0]
            time_end = inst_ava_duration[1]
            for time_duration in time_list:
                if time_begin >= time_duration[1] or time_end <= time_duration[0]:
                    continue
                time_begin = max(time_begin, time_duration[0])
                time_end = min(time_end, time_duration[1])
                result.append({"begin": time_begin.strftime(
                    TIME_FORMAT), "end": time_end.strftime(TIME_FORMAT)})
        aval.append({"pk": instpk, "name": inst.name, "time": result})
    return aval, unaval


def get_room_from_time(userpk, instpk, begin_time, end_time):  # 给定时间段，获取房间的详情
    aval = []
    unaval = []

    inst = Instrument.objects.get(pk=instpk)

    inst_ava = get_inst_avaliability(userpk, instpk, begin_time, end_time)
    if len(inst_ava) == 1 and inst_ava[0]["type"] == "ok":  # 首先检查乐器是否可用
        ifinstava = True
    else:
        ifinstava = False
        ifforbidden = False
        forbidden_detail = -1
        for i in range(len(inst_ava)):
            if inst_ava[i]["type"] == "forbidden":
                ifforbidden = True
                if forbidden_detail == -1 or inst_ava[i]["status"] < forbidden_detail:
                    forbidden_detail = inst_ava[i]["status"]
            elif inst_ava[i]["type"] == "order":
                pass
        if ifforbidden:
            insttype = "forbidden"
            instdetail = ForbiddenInstrument.get_status_detail(
                forbidden_detail)
        else:
            insttype = "order"

    roomset = inst.room.all()

    for room in roomset:  # 对房间检查
        room_ava = get_room_avaliability(userpk, room.pk, begin_time, end_time)
        roominfo = {}
        roominfo["pk"] = room.pk
        roominfo["name"] = room.name

        if ifinstava == True:
            if len(room_ava) == 1 and room_ava[0]["type"] == "ok":
                aval.append(roominfo)
                roominfo["type"] = "ok"
            else:
                unaval.append(roominfo)
                ifforbidden = False
                forbidden_detail = -1
                for i in range(len(room_ava)):
                    if room_ava[i]["type"] == "forbidden":
                        ifforbidden = True
                        if forbidden_detail == -1 or room_ava[i]["status"] < forbidden_detail:
                            forbidden_detail = room_ava[i]["status"]
                    elif room_ava[i]["type"] == "order":
                        pass
                if ifforbidden:
                    roominfo["type"] = "room_" + "forbidden"
                    roominfo["detail"] = "room_" + ForbiddenRoom.get_status_detail(
                        forbidden_detail)
                else:
                    roominfo["type"] = "room_" + "order"
        else:
            unaval.append(roominfo)
            roominfo["type"] = "inst_" + insttype
            roominfo["detail"] = "inst_" + instdetail

    return aval, unaval


def get_time_from_room(userpk, instpk, roompk, begin_time, end_time):  # 给定房间，获取各时间段的可用情况
    aval = []
    unaval = []

    inst_ava = get_inst_avaliability(userpk, instpk, begin_time, end_time)

    for i in range(len(inst_ava)):
        i_begin = inst_ava[i]["time"]
        if i == len(inst_ava) - 1:
            i_end = end_time
        else:
            i_end = inst_ava[i+1]["time"]

        if inst_ava[i]["type"] == "forbidden":
            stampinfo = {}
            stampinfo["type"] = "inst_" + "forbidden"
            stampinfo["detail"] = "inst_" + ForbiddenInstrument.get_status_detail(
                inst_ava[i]["status"])
            stampinfo["begin_time"] = i_begin
            stampinfo["end_time"] = i_end
            unaval.append(stampinfo)
        elif inst_ava[i]["type"] == "order":
            stampinfo = {}
            stampinfo["type"] = "inst_" + "order"
            stampinfo["begin_time"] = i_begin
            stampinfo["end_time"] = i_end
            aval.append(stampinfo)
        else:
            room_ava = get_room_avaliability(userpk, roompk, i_begin, i_end)
            for j in range(len(room_ava)):
                stampinfo = {}
                stampinfo["begin_time"] = room_ava[j]["time"]
                if j == len(room_ava) - 1:
                    stampinfo["end_time"] = i_end
                else:
                    stampinfo["end_time"] = room_ava[j+1]["time"]

                stampinfo["type"] = room_ava[j]["type"]
                if stampinfo["type"] == "forbidden":
                    stampinfo["type"] = "room_" + stampinfo["type"]
                    stampinfo["detail"] = "room_" + \
                        ForbiddenRoom.get_status_detail(room_ava[j]["status"])
                    unaval.append(stampinfo)
                elif stampinfo["type"] == "order":
                    stampinfo["type"] = "room_" + stampinfo["type"]
                    unaval.append(stampinfo)
                elif stampinfo["type"] == "ok":
                    aval.append(stampinfo)

    return aval, unaval
