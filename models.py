from django.conf import settings
from django.db import models
from django.db.models.deletion import DO_NOTHING

class UserProfile(models.Model):
    profile = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
    )
    wxid = models.CharField(max_length = 64)
    group = models.ManyToManyField(
        "UserGroup",
        on_delete = DO_NOTHING,
    )
    def __str__(self) -> str:
        return self.profile.get_username()

class Room(models.Model):
    name = models.CharField(max_length = 10)
    inst = models.ForeignKey(
        "Instrument",
        on_delete = DO_NOTHING,
    )
    def __str__(self) -> str:
        return self.name

class Instrument(models.Model):
    name = models.CharField(max_length = 30)
    room = models.ForeignKey(
        "Room",
        on_delete = DO_NOTHING,
    )
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
        on_delete = DO_NOTHING,
    )
    room = models.ForeignKey(
        "Room",
        on_delete = DO_NOTHING,
        blank = True,
        null = True,
    )
    inst = models.ForeignKey(
        "Instrument",
        on_delete = DO_NOTHING,
        blank = True,
        null = True,
    )
    price = models.IntegerField(max_length = 4)
    def __str__(self) -> str:
        return "{0} {1} {2}".format(self.user.profile.get_username(), self.inst.name, self.room.name)

class Coupon(models.Model):
    user = models.ForeignKey(
        "UserProfile",
        on_delete = DO_NOTHING,
    )
    order = models.ForeignKey(
        "Order",
        on_delete = DO_NOTHING,
    )
    price = models.IntegerField(max_length = 4)

class Unavailability(models.Model):
    begin_time = models.TimeField()
    end_time = models.TimeField()
    group = models.ManyToManyField(
        "UserGroup",
        on_delete = DO_NOTHING,
    )

class UserGroup(models.Model):
    name = models.CharField(max_length = 30)
