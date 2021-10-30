from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    profile = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
    )
    wxid = models.CharField(max_length = 64)
    #group = models.ManyToManyField(
    #    "UserGroup",
    #)
    def __str__(self) -> str:
        return self.profile.get_username()

class Room(models.Model):
    name = models.CharField(max_length = 10)
    price = models.IntegerField(default = 0) # * price if "only" borrow room
    def __str__(self) -> str:
        return self.name

class Instrument(models.Model):
    name = models.CharField(max_length = 30)
    room = models.ForeignKey(
        "Room",
        on_delete = models.DO_NOTHING,
    )
    price = models.IntegerField(default = 0) # * default price
    def __str__(self) -> str:
        return self.name

class InstrumentType(models.Model):
    name = models.CharField(max_length = 30)
    inst = models.ForeignKey(
        "Instrument",
        on_delete = models.CASCADE,
    )
    def __str__(self) -> str:
        return self.name

class Order(models.Model):
    user = models.ForeignKey(
        "UserProfile",
        on_delete = models.DO_NOTHING,
    )
    room = models.ForeignKey(
        "Room",
        on_delete = models.DO_NOTHING,
        blank = True,
        null = True,
    )
    inst = models.ForeignKey(
        "Instrument",
        on_delete = models.DO_NOTHING,
        blank = True,
        null = True,
    )
    price = models.IntegerField(default = 0)
    def __str__(self) -> str:
        return "{0} {1} {2}".format(self.user.profile.get_username(), self.inst.name, self.room.name)

class Coupon(models.Model):
    user = models.ForeignKey(
        "UserProfile",
        on_delete = models.DO_NOTHING,
    )
    order = models.ForeignKey(
        "Order",
        on_delete = models.DO_NOTHING,
    )
    price = models.IntegerField(default = 0)

class Unavailability(models.Model):
    begin_time = models.TimeField()
    end_time = models.TimeField()
    group = models.ManyToManyField(
        "UserGroup",
    )

class UserGroup(models.Model):
    name = models.CharField(max_length = 30)

# * special price rules
class SpecialPrice(models.Model):
    price = models.IntegerField(default = 0)
    group = models.ForeignKey(
        "UserGroup",
        on_delete = models.DO_NOTHING
    )
    inst = models.ForeignKey(
        "Instrument",
        on_delete = models.DO_NOTHING
    )
    room = models.ForeignKey(
        "Room",
        on_delete = models.DO_NOTHING
    )

# * how to get price :
# 必须借房间
# 设置不选择乐器为一种price = 0的移动乐器
# input: (instrument, room, user)
# 1. 获取user的usergroup
# 2. 判断instrument是否为固定乐器
### 2.1如果instrument为固定乐器,let retprice = instruent.price
### 2.2如果instrument不是固定乐器（移动乐器）,let retprice = instrument.price + room.price
# 3. 暂定：枚举room下所有SpecialPrice s: (总之就是通过某种方法找special price)
### 3.1 如果s满足s.group = usergroup, s.inst = instrument, let retprice = min(retprice, s.price)
# 4. 返回retprice

