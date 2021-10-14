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
    def __str__(self) -> str:
        return self.name

class Instrument(models.Model):
    name = models.CharField(max_length = 30)
    room = models.ForeignKey(
        "Room",
        on_delete = models.DO_NOTHING,
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
    price = models.IntegerField()
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
    price = models.IntegerField()

class Unavailability(models.Model):
    begin_time = models.TimeField()
    end_time = models.TimeField()
    group = models.ManyToManyField(
        "UserGroup",
    )

class UserGroup(models.Model):
    name = models.CharField(max_length = 30)
