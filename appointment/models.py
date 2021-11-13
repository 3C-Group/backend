import datetime
from django.conf import settings
from django.db import models


# --- managers ---
class TypeManager(models.Manager):
    def create_type(self, name):
        type = self.create(name=name)
        return type.pk  # 返回创建的"乐器类型"的pk


class InstManager(models.Manager):
    def create_inst(self, name, typepk):
        insttype = InstrumentType.objects.get(pk=typepk)
        inst = self.create(name=name, type=insttype)
        return inst.pk


class RoomManager(models.Manager):
    def create_room(self, name, max_inst):
        room = self.create(name=name, max_inst=max_inst)
        return room.pk


class UserGroupManager(models.Manager):
    def create_group(self, name):
        group = self.create(name=name)
        return group.pk


class UserProfileManager(models.Manager):
    def create_user(self, openid, status, thuid="default-thuid"):
        user = self.create(openid=openid, status=status, thuid=thuid)
        return user.pk


class InstrumentTypePriceManager(models.Manager):
    def create_type_price(self, grouppk, typepk, price):
        group = UserGroup.objects.get(pk=grouppk)
        insttype = InstrumentType.objects.get(pk=typepk)
        typeprice = self.create(group=group, insttype=insttype, price=price)
        return typeprice.pk


class RoomPriceManager(models.Manager):
    def create_room_price(self, grouppk, roompk, price):
        group = UserGroup.objects.get(pk=grouppk)
        room = Room.objects.get(pk=roompk)
        roomprice = self.create(group=group, room=room, price=price)
        return roomprice.pk


class ForbiddenRoomManager(models.Manager):
    def create_rule(self, grouppk, roompk, begin_time, end_time, status):
        group = UserGroup.objects.get(pk=grouppk)
        room = Room.objects.get(pk=roompk)
        rule = self.create(
            group=group, room=room, begin_time=begin_time, end_time=end_time, status=status)
        return rule.pk


class OrderManager(models.Manager):
    def create_order(self, userpk, roompk, instpk, price,  begin_time, end_time):
        user = UserProfile.objects.get(pk=userpk)
        room = Room.objects.get(pk=roompk)
        inst = Instrument.objects.get(pk=instpk)
        status = Order.Status.UNPAID  # 默认未支付
        order = self.create(user=user, room=room, inst=inst, status=status,
                            begin_time=begin_time, end_time=end_time, price=price)
        return order.pk


# --- models ---


class UserProfile(models.Model):
    thuid = models.CharField(
        max_length=64, default="default-thuid")  # thu身份验证到具体人
    openid = models.CharField(
        max_length=64, default="default-openid")  # 用openid确认微信用户
    balance = models.IntegerField(default=0)  # 余额
    group = models.ManyToManyField("UserGroup", )

    class Status(models.IntegerChoices):
        STUDENT = 1         # 24岁，是学生
        TEACHER = 2         # 是老师
        OTHER = 3           # 不知道是个啥，可能是邱宝？
        UNAUTHORIZED = 100  # 未验证身份的用户

    status = models.IntegerField(
        choices=Status.choices, default=Status.UNAUTHORIZED)

    def __str__(self) -> str:
        return self.openid
    objects = UserProfileManager()


class Room(models.Model):
    name = models.CharField(max_length=20)
    max_inst = models.IntegerField(default=1)  # 房屋最多可以放置多少乐器
    img = models.ImageField(default="media/room/default_room.png",
                            upload_to='room/')  # 房间的照片

    def __str__(self) -> str:
        return self.name

    objects = RoomManager()


class Instrument(models.Model):
    name = models.CharField(max_length=30)
    room = models.ManyToManyField(  # 可以去往的房间
        "Room", )
    type = models.ForeignKey(  # 乐器类型
        "InstrumentType",
        on_delete=models.CASCADE,
    )
    img = models.ImageField(default="media/inst/default_inst.png",
                            upload_to='inst/')  # 房间的照片

    def __str__(self) -> str:
        return self.name

    objects = InstManager()


class InstrumentType(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self) -> str:
        return self.name

    objects = TypeManager()


class Order(models.Model):
    begin_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    user = models.ForeignKey(
        "UserProfile",
        on_delete=models.DO_NOTHING,
    )
    room = models.ForeignKey(
        "Room",
        on_delete=models.DO_NOTHING,
        blank=True,
    )
    inst = models.ForeignKey(
        "Instrument",
        on_delete=models.DO_NOTHING,
        blank=True,
    )
    price = models.IntegerField(default=0)  # 原价
    paid = models.IntegerField(default=0)  # 实际支付的金额

    class Status(models.IntegerChoices):
        UNPAID = 1     # 未支付
        PAID = 2       # 已支付但未使用
        CANCELLED = 3  # 已取消 分两种情况 支付或未支付 支付后手动取消的要将付款返到余额里
        FINISHED = 4   # 已完成 完成后不可再取消
        OUTDATED = 5   # 已支付 但未使用 不可取消

    status = models.IntegerField(choices=Status.choices, default=Status.UNPAID)

    def __str__(self) -> str:
        return "{0} {1} {2}".format(self.user.openid,
                                    self.inst.name, self.room.name)
    objects = OrderManager()


class Unavailability(models.Model):
    begin_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))


class UserGroup(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self) -> str:
        return self.name

    objects = UserGroupManager()


class RoomPrice(models.Model):  # 房间价格
    price = models.IntegerField(default=0)
    group = models.ForeignKey(  # 特殊规则针对的单个用户组
        "UserGroup",
        on_delete=models.CASCADE,
    )
    room = models.ForeignKey(
        "Room",
        on_delete=models.CASCADE,
    )
    objects = RoomPriceManager()


class InstrumentTypePrice(models.Model):  # 乐器类型的价格
    price = models.IntegerField(default=0)
    group = models.ForeignKey(  # 特殊规则针对的单个用户组
        "UserGroup",
        on_delete=models.CASCADE,
    )
    insttype = models.ForeignKey(
        "InstrumentType",
        on_delete=models.CASCADE,
    )
    objects = InstrumentTypePriceManager()


class ForbiddenRoom(models.Model):  # 对于（用户组，房间，时间段），进行禁用
    group = models.ForeignKey(
        "UserGroup",
        on_delete=models.CASCADE,
    )
    room = models.ForeignKey(
        "Room",
        on_delete=models.CASCADE,
    )
    begin_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))

    class Status(models.IntegerChoices):
        FIX = 1       # 维修中
        ACTIVITY = 2  # 活动占用
        OTHER = 100   # 其他

    status = models.IntegerField(choices=Status.choices,
                                 default=Status.FIX)

    objects = ForbiddenRoomManager()


class ForbiddenInstrument(models.Model):  # 对于（用户组，乐器，时间段），进行禁用
    group = models.ForeignKey(  # 禁用乐器类型
        "UserGroup",
        on_delete=models.CASCADE,
    )
    inst = models.ForeignKey(
        "Instrument",
        on_delete=models.CASCADE,
    )
    begin_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))

    class Status(models.IntegerChoices):
        FIX = 1  # 维修
        ACTIVITY = 2  # 活动占用
        OTHER = 100  # 其他

    status = models.IntegerField(choices=Status.choices,
                                 default=Status.FIX)


# 检查占用：
# 0. 检查是否被forbidden
# 1. 通过枚举相关order确定每个时刻占用乐器数量
# 2. 将某时刻占用乐器数量，与最大同时占用数量进行比较

# 检查价格
# input: (instrument, room, user)
# 0. instrument -> instruemtnType ; user - > usergroup
# 1. (usergroup, instruemntType)获取最低inst.price
# 2. (usergroup, room)获取最低room.price
# 3. room.price+inst.price得到final.price
