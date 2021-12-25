from django.test import TestCase
from appointment.models import *
from appointment.views import *

# Create your tests here.


class RoomTest(TestCase):
    def test_get_info(self):
        ret = type_service.get_inst_type_info()
        self.assertIsNotNone(ret)

        ret = inst_service.get_inst_info()
        self.assertIsNotNone(ret)

        ret = room_service.get_room_info()
        self.assertIsNotNone(ret)

        ret = usergroup_service.get_group_info()
        self.assertIsNotNone(ret)

    def test_get(self):
        ret = json.loads(verify_token(
            {"openid": "openid", "token": "not-valid"}))
        self.assertEqual(1, ret["userpk"])
        self.assertEqual("OTHER", ret["status"])

        ret = price_service.get_price(1, 1, 1)
        self.assertEqual(-1, ret)

        ret = type_service.get_room_for_type({
            "userpk": 1,
            "roompk": 1,
            "typepk": 1
        })
        self.assertJSONEqual(ret, {"roomnum": 0, "data": []},)

        ret = json.loads(inst_service.get_inst_for_type(1))
        self.assertEqual(ret["instnum"], 1)

        room = Room.objects.create_room("room", 1, "this is a room")
        insttype = InstrumentType.objects.create_type("钢琴")
        inst = Instrument.objects.create_inst("黑色的钢琴", insttype, "好听的声音")

        ret = json.loads(order_service.get_order({"orderpk": 1}))
        self.assertEqual(0, ret["allnum"])

        ret = json.loads(user_service.get_user(
            {"openid": "openid", "status": "UNAUTHORIZED", "grouppk": 3}))
        self.assertEqual(2, len(ret))

        temppk = InstrumentType.objects.create_type("temp")
        ret = type_service.update_type({"pk": temppk, "name": "xxx"})
        self.assertEqual("success", ret)

        ret = type_service.delete_type(temppk)
        self.assertEqual(ret, True)

        temppk = Instrument.objects.create_inst("temp", 2, "")
        ret = inst_service.update_inst({"pk": temppk, "name": "xxx"})
        self.assertEqual("success", ret)

        ret = inst_service.delete_inst(temppk)
        self.assertEqual(ret, "success")

        temppk = Room.objects.create_room("temp", 1, "")
        ret = room_service.update_room(
            {"pk": temppk, "name": "xxx", "max_inst": 100})
        self.assertEqual("success", ret)

        ret = room_service.delete_room(temppk)
        self.assertEqual(ret, "success")

        ret = inst_service.add_inst_to_room(inst, room)
        self.assertEqual("success", ret)
        ret = inst_service.add_inst_to_room(inst, room)
        self.assertEqual("exist", ret)
        ret = inst_service.remove_inst_from_room(inst, room)
        self.assertEqual("success", ret)
        ret = inst_service.remove_inst_from_room(inst, room)
        self.assertEqual("notexist", ret)

        group = UserGroup.objects.create_group("TestGroup")
        ret = usergroup_service.update_group({"pk": group, "name": "xxx"})
        self.assertEqual("success", ret)

        group = UserGroup.objects.create_group("TestGroup")
        ret = user_service.set_usergroup(1, group)
        self.assertEqual(ret, "success")
        ret = user_service.set_usergroup(1, group)
        self.assertEqual(ret, "exist")
        ret = user_service.set_usergroup(1, 2)
        self.assertEqual(ret, "forbidden")
        ret = user_service.unset_usergroup(1, 2)
        self.assertEqual(ret, "forbidden")
        ret = user_service.unset_usergroup(1, group)
        self.assertEqual(ret, "success")
        ret = user_service.unset_usergroup(1, group)
        self.assertEqual(ret, "notexist")

        ret = usergroup_service.delete_group(group)
        self.assertEqual(ret, "success")

        ret = usergroup_service.delete_group(1)
        self.assertEqual("forbidden", ret)

        ret = price_service.set_type_price(3, insttype, 10)
        ret = price_service.set_room_price(3, room, 20)

        ret = json.loads(price_service.get_all_price_for_type(insttype))
        for t in ret:
            if t["grouppk"] == 3:
                self.assertEqual(10, t["price"])

        ret = json.loads(price_service.get_all_price_for_room(room))
        for t in ret:
            if t["grouppk"] == 3:
                self.assertEqual(20, t["price"])

        ret = room_service.set_room_forbidden({
            "roompk": 1,
            "usergrouppk": 1,
            "begin_time": "2023/9/24 11:50",
            "end_time": "2023/9/24 12:01",
            "status": 1
        })
        self.assertEqual(ret, "forbidden")
        temppk = room_service.set_room_forbidden({
            "roompk": 2,
            "usergrouppk": 1,
            "begin_time": "2023/9/24 11:50",
            "end_time": "2023/9/24 12:01",
            "status": 1
        })
        ret = room_service.set_room_forbidden({
            "roompk": 2,
            "usergrouppk": 1,
            "begin_time": "2023/9/24 11:50",
            "end_time": "2023/9/24 12:01",
            "status": 1
        })
        self.assertEqual(ret, "already forbidden")
        ret = json.loads(room_service.get_room_forbidden({}))
        self.assertEqual(ret["allnum"], 1)
        ret = room_service.unset_room_forbidden(temppk)
        self.assertEqual(ret, True)

        ret = inst_service.set_inst_forbidden({
            "instpk": 1,
            "usergrouppk": 1,
            "begin_time": "2023/9/24 11:50",
            "end_time": "2023/9/24 12:01",
            "status": 1
        })
        self.assertEqual(ret, "forbidden")
        temppk = inst_service.set_inst_forbidden({
            "instpk": 2,
            "usergrouppk": 1,
            "begin_time": "2023/9/24 11:50",
            "end_time": "2023/9/24 12:01",
            "status": 1
        })
        ret = inst_service.set_inst_forbidden({
            "instpk": 2,
            "usergrouppk": 1,
            "begin_time": "2023/9/24 11:50",
            "end_time": "2023/9/24 12:01",
            "status": 1
        })
        self.assertEqual(ret, "already forbidden")
        ret = json.loads(inst_service.get_inst_forbidden({}))
        self.assertEqual(ret["allnum"], 1)
        ret = inst_service.unset_inst_forbidden(temppk)
        self.assertEqual(ret, True)

        ret = inst_service.add_inst_to_room(inst, room)

        today = datetime.datetime.now() + datetime.timedelta(days=1)
        st = datetime.datetime(today.year, today.month, today.day, 10, 0, 0)
        ed = st + datetime.timedelta(hours=2)

        st_1 = st - datetime.timedelta(hours=1)
        ed_1 = ed + datetime.timedelta(hours=1)

        st_time = datetime.datetime.strftime(st, TIME_FORMAT)
        ed_time = datetime.datetime.strftime(ed, TIME_FORMAT)

        orderpk = order_service.create_order(
            {"begin_time": st_time, "end_time": ed_time, "userpk": 1, "roompk": room, "instpk": inst})

        ret = order_service.create_order(
            {"begin_time": st_time, "end_time": ed_time, "userpk": 1, "roompk": room, "instpk": inst})
        self.assertEqual(ret, "inst order conflict")

        ret = json.loads(order_service.get_order({"userpk": 1}))
        order_service.get_all_order()
        self.assertEqual(1, ret["allnum"])

        ret = order_service.pay_order(orderpk)
        ret = order_service.cancel_order(orderpk)
        self.assertEqual(ret, True)

        orderpk = order_service.create_order(
            {"begin_time": st_time, "end_time": ed_time, "userpk": 1, "roompk": room, "instpk": inst})

        st_1 = datetime.datetime.strftime(st_1, TIME_FORMAT)
        ed_1 = datetime.datetime.strftime(ed_1, TIME_FORMAT)
        ret = ava_service.get_room_availability(1, room, st_1, ed_1)
        self.assertEqual(len(ret), 3)

        noticepk = notice_service.create_notice(
            "title", "content", "author", st_1, None)
        ret = json.loads(notice_service.get_all_notice())
        self.assertEqual(len(ret), 1)
        ret = notice_service.modify_notice(
            noticepk, "title", "content", "author", ed_1, None)
        self.assertEqual(ret, "success")
        ret = notice_service.delete_notice(noticepk)
        self.assertEqual(ret, "success")

        aval, unaval = ava_service.get_inst_avalist(1, insttype, st_1, ed_1)
        self.assertEqual(len(aval), 1)
        self.assertEqual(len(unaval), 0)

        aval, _, avalroom, _ = ava_service.get_single_inst_avalist(
            1, inst, st_1, ed_1)

        self.assertEqual(len(aval), 2)
        self.assertEqual(len(avalroom), 1)

        aval, unaval = ava_service.get_room_from_time(1, inst, st_1, ed_1)
        self.assertEqual(len(aval), 0)
        self.assertEqual(len(unaval), 1)

        aval, unaval = ava_service.get_time_from_room(
            1, inst, room, st_1, ed_1)
        self.assertEqual(len(aval), 2)
        self.assertEqual(len(unaval), 1)

        ret = user_service.add_balance(1, -1)
        self.assertEqual(ret, "forbidden")
        ret = user_service.add_balance(1, 200)
        self.assertEqual(ret, "success")
        ret = user_service.get_balance(1)
        self.assertEqual(ret, 200)

        ret = json.loads(order_service.get_order_in_range(0, 10))
        self.assertEqual(len(ret), 2)
