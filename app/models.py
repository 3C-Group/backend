import datetime
from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    profile = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
    )
    wxid = models.CharField(max_length = 64)
    balance = models.IntegerField(default = 0)
    group = models.ManyToManyField(
        "UserGroup",
    )
    def __str__(self) -> str:
        return self.profile.get_username()

class Room(models.Model):
    name = models.CharField(max_length = 10)
    price = models.IntegerField(default = 0) # 房屋的默认价格
    maxInst = models.IntegerField(default = 1) # 房屋最多可以放置多少乐器
    def __str__(self) -> str:
        return self.name

class Instrument(models.Model):
    name = models.CharField(max_length = 30)
    price = models.IntegerField(default = 0) # 音乐的默认价格
    room = models.ManyToManyField( # 可以去往的房间
        "Room", 
    )
    type = models.ForeignKey( # 乐器类型
        "InstrumentType",
        on_delete = models.CASCADE,
    )
    def __str__(self) -> str:
        return self.name

class TypeManager(models.Manager):
    def create_type(self, name):
        type = self.create(name = name)
        return type

class InstrumentType(models.Model):
    name = models.CharField(max_length = 30)
    def __str__(self) -> str:
        return self.name
    objects = TypeManager()

class Order(models.Model):
    begin_time = models.DateTimeField(default = datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default = datetime.datetime(1, 1, 1))
    user = models.ForeignKey(
        "UserProfile",
        on_delete = models.DO_NOTHING,
    )
    room = models.ForeignKey(
        "Room",
        on_delete = models.DO_NOTHING,
        blank = True,
    )
    inst = models.ForeignKey(
        "Instrument",
        on_delete = models.DO_NOTHING,
        blank = True,
    )
    price = models.IntegerField(default = 0) # 原价
    paid = models.IntegerField(default = 0)  # 实际支付的金额
    class Status(models.IntegerChoices):
        UNPAID = 1     # 未支付
        PAID = 2       # 已支付但未使用
        CANCELLED = 3  # 已取消 分两种情况 支付或未支付 支付后手动取消的要将付款返到余额里
        FINISHED = 4   # 已完成 完成后不可再取消
        OUTDATED = 5   # 已支付 但未使用 不可取消
    status = models.IntegerField(choices = Status.choices, default = Status.UNPAID)
    def __str__(self) -> str:
        return "{0} {1} {2}".format(self.user.profile.get_username(), self.inst.name, self.room.name)

class Unavailability(models.Model):
    begin_time = models.DateTimeField(default = datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default = datetime.datetime(1, 1, 1))

class UserGroup(models.Model):
    name = models.CharField(max_length = 30)
    def __str__(self) -> str:
        return self.name

# 特殊规则
class SpecialPrice(models.Model):
    price = models.IntegerField(default = 0) # 符合该特殊规则，可以采用的具体价格
    group = models.ForeignKey( # 特殊规则针对的单个用户组 
        "UserGroup",
        on_delete = models.CASCADE,
    )
    inst = models.ForeignKey( 
    # 特殊规则针对的某个乐器 / 某个乐器类型(添加通配某类型的通配乐器) / 所有乐器(添加通配所有乐器的通配乐器) 
    # OR: 采用其他字段来存储是否通配
        "Instrument",
        on_delete = models.CASCADE,
    )
    room = models.ForeignKey( 
    # 特殊规则针对的单个房间 / 所有房间(添加通配所有房间的通配房间)
    # OR: 采用其他字段来存储是否通配
        "Room",
        on_delete = models.CASCADE,
    )

# 检查占用：
# 1. 通过枚举相关order确定每个时刻占用乐器数量
# 2. 将某时刻占用乐器数量，与最大同时占用数量进行比较

# 检查价格
# input: (instrument, room, user)
# 1. room.price+inst.price得到通用价格
# 2. 考虑每一个符合input的特殊规则，在所有价格里取min

# 禁用房间：
# 1. 赋予该规则一个负数价格
# 2. 如果某个input检查价格得到了负数，说明它被某规则禁用