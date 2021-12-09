from django.urls import path
from . import views

urlpatterns = [
    path("index/", views.index, name="index"),
    # 测试图片用
    path("view/", views.testview, name="testview"),
    path("test_upload/", views.test_upload, name="test_upload_image"),

    path("token/", views.get_token, name="get_token"),

    #  乐器管理
    path("manage/inst/", views.manage_inst, name="manage_inst"),
    #  房间管理
    path("manage/room/", views.manage_room, name="manage_room"),
    #  乐器类型的管理
    path("manage/type/", views.manage_type, name="manage_type"),
    # 房间与乐器的关系管理
    path("manage/inst_room/", views.manage_inst_to_room, name="manage_inst_room"),
    # 用户组管理
    path("manage/usergroup/", views.manage_usergroup, name="manage_usergroup"),
    # 用户管理
    path("manage/user/", views.manage_user, name="manage_user"),
    # 管理订单
    path("manage/order/", views.manage_order, name="manage_order"),

    # 用户与用户组的关系管理
    path("manage/user_to_group/", views.manage_user_to_group,
         name="manage_user_to_group"),

    # 乐器类型与用户价格的设置
    path("manage/type_price/", views.manage_type_price, name="manage_type_price"),
    # 房间与用户价格的设置
    path("manage/room_price/", views.manage_room_price, name="manage_room_price"),
    # 房间对某些用户组关闭
    path("manage/room_use/", views.manage_room_use, name="manage_room_use"),
    # 乐器对某些用户组关闭
    path("manage/inst_use/", views.manage_inst_use, name="manage_inst_use"),

    # 管理用户余额
    path("manage/user_balance/", views.manage_user_balance,
         name="manage_user_balance"),

    path("set_room_image/", views.set_room_image, name="set_room_image"),
    # 设置房间的image

    #  信息获取
    path("get_type/", views.get_type, name="get_type"),  # 获取所有的乐器类型信息
    path("get_inst/", views.get_inst, name="get_inst"),  # 获取所有的乐器信息
    path("get_room/", views.get_room, name="get_room"),  # 获取所有的房间信息
    path("get_usergroup/", views.get_usergroup,
         name="get_usergroup"),  # 获取所有的用户组信息
    path("get_user/", views.get_user, name="get_user"),  # 获得所有用户信息
    path("get_price/", views.get_price, name="get_price"),  # 获取（用户，房间，乐器）三元组的最低价格
    path("get_room_avalilability/", views.get_room_avalilability,
         name="get_room_avalilability"),  # 获取一段时间的房间可用性
    path("get_order/", views.get_order, name="get_order"),  # 获取所有的订单信息
    path("get_room_for_type/", views.get_room_for_type,
         name="get_room_for_type"),  # 获取某类型的可用房间
    path("get_inst_for_type/", views.get_inst_for_type,
         name="get_inst_for_type"),  # 获取某类型的所有乐器
    path("get_type_availability/", views.get_type_availability,
         name="get_type_availability"),  # 获取某类型的可用性
    path("get_room_from_time/", views.get_room_from_time,
         name="get_room_from_time"),  # 获取某时间段，针对特定乐器与用户的房间可用性
    path("get_time_from_room/", views.get_time_from_room,
         name="get_time_from_room"),  # 获取某房间与乐器组的，各时间段可用性
    path("get_order_in_range/", views.get_order_in_range,
         name="get_order_in_range"),  # 获取按开始时间的order在[begin, end)范围内的order
]
