import datetime
from django.conf import settings
from django.db import models
from django.db.models.fields import CharField
from .myutils import get_md5_8th
TIME_FORMAT = '%Y/%m/%d %H:%M'  # 时间格式

# --- managers ---

# get_dict : 为了综合浏览所有信息时的格式化
# get_detail : 获取某个模型的完全详情信息


class TypeManager(models.Manager):
    def create_type(self, name):
        type = self.create(name=name)
        return type.pk  # 返回创建的"乐器类型"的pk


class InstManager(models.Manager):
    def create_inst(self, name, typepk, des):
        insttype = InstrumentType.objects.get(pk=typepk)
        inst = self.create(name=name, type=insttype, description=des)
        return inst.pk


class RoomManager(models.Manager):
    def create_room(self, name, max_inst, des):
        room = self.create(name=name, max_inst=max_inst, description=des)
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


class ForbiddenInstrumentManager(models.Manager):
    def create_rule(self, grouppk, instpk, begin_time, end_time, status):
        group = UserGroup.objects.get(pk=grouppk)
        inst = Instrument.objects.get(pk=instpk)
        rule = self.create(
            group=group, inst=inst, begin_time=begin_time, end_time=end_time, status=status)
        return rule.pk


class OrderManager(models.Manager):
    def create_order(self, userpk, roompk, instpk, price, begin_time, end_time):
        user = UserProfile.objects.get(pk=userpk)
        room = Room.objects.get(pk=roompk)
        inst = Instrument.objects.get(pk=instpk)
        status = Order.Status.UNPAID  # 默认未支付
        order = self.create(user=user, room=room, inst=inst, status=status,
                            begin_time=begin_time, end_time=end_time, price=price)
        hash = get_md5_8th(order.pk)
        order.hash = hash
        order.save()
        return order


class NoticeManager(models.Manager):
    def create_notice(self, title, content, author, time):
        notice = self.create(title=title, content=content,
                             author=author, time=time, file=None)
        return notice.pk

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
        UNAUTHORIZED = 100  # 未验证身份的用户

    status = models.IntegerField(
        choices=Status.choices, default=Status.UNAUTHORIZED)

    def get_dict(self):
        info = {}
        info["pk"] = self.pk
        info["balance"] = self.balance
        info["usergroup"] = [group.pk for group in self.group.all()]
        if self.status == self.Status.STUDENT:
            info["status"] = "STUDENT"
        elif self.status == self.Status.TEACHER:
            info["status"] = "TEACHER"
        else:
            info["status"] = "UNAUTHORIZED"
        info["openid"] = self.openid
        info["thuid"] = self.thuid
        return info

    def add_balance(self, money):
        self.balance = self.balance + money
        self.save()
        return

    def __str__(self) -> str:
        return "{0} {1}".format(self.openid, self.thuid)
    objects = UserProfileManager()


class Room(models.Model):
    name = models.CharField(max_length=20, unique=True)
    max_inst = models.IntegerField(default=1)  # 房屋最多可以放置多少乐器
    img = models.ImageField(default="room/default_room.png",
                            upload_to='room/')  # 房间的照片
    description = models.CharField(default="", max_length=1000)

    def __str__(self) -> str:
        return self.name

    def get_dict(self) -> dict:
        roominfo = {}
        roominfo["pk"] = self.pk
        roominfo["name"] = self.name
        roominfo["max_inst"] = self.max_inst
        roominfo["img"] = self.img.url
        roominfo["inst"] = [inst.pk for inst in Room.objects.get(
            pk=self.pk).instrument_set.all()]  # 所有可到访的乐器
        roominfo["description"] = self.description
        return roominfo

    objects = RoomManager()


class Instrument(models.Model):
    name = models.CharField(max_length=30, unique=True)
    room = models.ManyToManyField(  # 可以去往的房间
        "Room", )
    type = models.ForeignKey(  # 乐器类型
        "InstrumentType",
        on_delete=models.CASCADE,
    )
    img = models.ImageField(default="inst/default_inst.png",
                            upload_to='inst/')  # 房间的照片
    description = models.CharField(default="", max_length=1000)

    def __str__(self) -> str:
        return self.name

    def get_dict(self) -> dict:
        instinfo = {}
        instinfo["pk"] = self.pk
        instinfo["img"] = self.img.url
        instinfo["name"] = self.name
        instinfo["typepk"] = self.type.pk
        instinfo["typename"] = InstrumentType.objects.get(
            pk=instinfo["typepk"]).name  # 获取该乐器对应的乐器类型的名称
        instinfo["roompk"] = [rm.pk for rm in self.room.all()]
        instinfo["roomname"] = [rm.name for rm in self.room.all()]
        instinfo["roomdescription"] = [
            rm.description for rm in self.room.all()]
        instinfo["roomnum"] = len(instinfo["roompk"])
        instinfo["description"] = self.description
        return instinfo

    objects = InstManager()


class InstrumentType(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return self.name

    def get_dict(self) -> dict:
        typeinfo = {}
        typeinfo["pk"] = self.pk
        typeinfo["name"] = self.name
        return typeinfo

    objects = TypeManager()


class Order(models.Model):
    begin_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    created_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        "UserProfile",
        on_delete=models.DO_NOTHING,
    )
    room = models.ForeignKey(
        "Room",
        on_delete=models.DO_NOTHING,
    )
    inst = models.ForeignKey(
        "Instrument",
        on_delete=models.DO_NOTHING,
    )
    price = models.IntegerField(default=0)  # 原价
    paid = models.IntegerField(default=0)   # 实际支付的金额
    hash = models.CharField(max_length=8, default="default", unique=True)

    class Status(models.IntegerChoices):
        UNPAID = 1     # 未支付
        PAID = 2       # 已支付但未使用
        CANCELLED = 3  # 已取消 分两种情况 支付或未支付 支付后手动取消的要将付款返到余额里
        FINISHED = 4   # 已完成 完成后不可再取消
        OUTDATED = 5   # 已支付 但未使用 不可取消

    status = models.IntegerField(choices=Status.choices, default=Status.UNPAID)

    def get_dict(self) -> dict:  # 返回格式化后的dict
        item_data = {}
        item_data["pk"] = self.pk
        item_data["begin_time"] = datetime.datetime.strftime(
            self.begin_time, TIME_FORMAT)
        item_data["end_time"] = datetime.datetime.strftime(
            self.end_time, TIME_FORMAT)
        item_data["userpk"] = self.user.pk
        item_data["roompk"] = self.room.pk
        item_data["instpk"] = self.inst.pk
        item_data["price"] = self.price
        item_data["paid"] = self.paid
        item_data["hash"] = self.hash
        item_data["room_name"] = Room.objects.get(pk=self.room.pk).name
        item_data["inst_name"] = Instrument.objects.get(pk=self.inst.pk).name
        item_data["user_openid"] = UserProfile.objects.get(
            pk=self.user.pk).openid
        if self.status == self.Status.UNPAID:
            item_data["status"] = "UNPAID"
        elif self.status == self.Status.PAID:
            item_data["status"] = "PAID"
        elif self.status == self.Status.CANCELLED:
            item_data["status"] = "CANCELLED"
        elif self.status == self.Status.FINISHED:
            item_data["status"] = "FINISHED"
        elif self.status == self.Status.OUTDATED:
            item_data["status"] = "OUTDATED"
        return item_data

    def __str__(self) -> str:
        return "{0} {1} {2} {3}".format(self.user.openid, self.user.thuid,
                                        self.inst.name, self.room.name)
    objects = OrderManager()


class Unavailability(models.Model):
    begin_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    end_time = models.DateTimeField(default=datetime.datetime(1, 1, 1))


class UserGroup(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return self.name

    def get_dict(self) -> dict:
        info = {}
        info["pk"] = self.pk
        info["name"] = self.name
        return info

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

    def get_dict(self):
        info = {}
        info["pk"] = self.pk
        info["group"] = self.group.pk
        info["room"] = self.room.pk
        info["begin_time"] = datetime.datetime.strftime(
            self.begin_time, TIME_FORMAT)
        info["end_time"] = datetime.datetime.strftime(
            self.end_time, TIME_FORMAT)
        info["status"] = self.get_status_detail(self.status)
        return info

    @classmethod
    def get_status_detail(cls, arg):
        if arg == cls.Status.FIX:
            return "FIX"
        elif arg == cls.Status.ACTIVITY:
            return "ACTIVITY"
        else:
            return "OTHER"


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

    objects = ForbiddenInstrumentManager()

    def get_dict(self):
        info = {}
        info["pk"] = self.pk
        info["group"] = self.group.pk
        info["inst"] = self.inst.pk
        info["begin_time"] = datetime.datetime.strftime(
            self.begin_time, TIME_FORMAT)
        info["end_time"] = datetime.datetime.strftime(
            self.end_time, TIME_FORMAT)
        info["status"] = self.get_status_detail(self.status)
        return info

    @classmethod
    def get_status_detail(cls, arg):
        if arg == cls.Status.FIX:
            return "FIX"
        elif arg == cls.Status.ACTIVITY:
            return "ACTIVITY"
        else:
            return "OTHER"


class Notice(models.Model):
    title = models.CharField(max_length=30)
    content = models.CharField(max_length=1000)
    author = models.CharField(max_length=30)
    file = models.FileField(upload_to="file/", default="file/NONE.txt")
    time = models.DateTimeField(default=datetime.datetime(1, 1, 1))  # 发布时间
    filename = models.CharField(max_length=100, default="")

    objects = NoticeManager()

    def get_dict(self):
        noticeinfo = {}
        noticeinfo["pk"] = self.pk
        noticeinfo["title"] = self.title
        noticeinfo["content"] = self.content
        noticeinfo["author"] = self.author
        noticeinfo["time"] = datetime.datetime.strftime(self.time, TIME_FORMAT)
        noticeinfo["file"] = self.file.url if self.file else None
        noticeinfo["filename"] = self.filename if self.file else None
        return noticeinfo


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
