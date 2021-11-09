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


# --- models ---
class UserProfile(models.Model):
    profile = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    wxid = models.CharField(max_length=64)
    balance = models.IntegerField(default=0)
    group = models.ManyToManyField("UserGroup", )

    def __str__(self) -> str:
        return self.profile.get_username()


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
        UNPAID = 1  # 未支付
        PAID = 2  # 已支付但未使用
        CANCELLED = 3  # 已取消 分两种情况 支付或未支付 支付后手动取消的要将付款返到余额里
        FINISHED = 4  # 已完成 完成后不可再取消
        OUTDATED = 5  # 已支付 但未使用 不可取消

    status = models.IntegerField(choices=Status.choices, default=Status.UNPAID)

    def __str__(self) -> str:
        return "{0} {1} {2}".format(self.user.profile.get_username(),
                                    self.inst.name, self.room.name)


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


class InstrumentTypePrice(models.Model):  # 乐器类型的价格
    price = models.IntegerField(default=0)
    group = models.ForeignKey(  # 特殊规则针对的单个用户组
        "UserGroup",
        on_delete=models.CASCADE,
    )
    inst = models.ForeignKey(
        "InstrumentType",
        on_delete=models.CASCADE,
    )


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
        FIX = 1  # 维修中
        ACTIVITY = 2  # 活动占用
        OTHER = 100  # 其他

    status = models.IntegerField(choices=Status.choices,
                                 default=Status.ACTIVITY)


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
        ACTIVITY = 1  # 活动占用
        FIX = 2  # 维修
        OTHER = 100  # 其他

    status = models.IntegerField(choices=Status.choices,
                                 default=Status.ACTIVITY)


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
