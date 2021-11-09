from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='index'),

    # 测试用试图
    path('view/', views.testview, name='testview'),
    path('test_upload/', views.test_upload, name='test_upload_iamge'),

    #  乐器管理
    path('manage/inst/add/', views.add_inst, name='add_inst'),
    path('manage/inst/delete/', views.delete_inst, name='delete_inst'),

    #  房间管理
    path('manage/room/add/', views.add_room, name='add_room'),
    path('manage/room/delete/', views.delete_room, name='delete_room'),

    #  乐器类型的管理
    path('manage/type/add/', views.add_type, name='manage_type'),
    path('manage/type/delete/', views.delete_type, name='delete_type'),

    # 房间与乐器的关系管理
    path('manage/add_inst_to_room', views.add_inst_to_room, name="add_inst_to_room"),  # 将乐器加入房间
    path('manage/remove_inst_from_room', views.remove_inst_from_room, name="remove_inst_from_room"),  # 将乐器从房间中移除
    path('manage/remove_inst_from_all', views.remove_inst_from_all, name="remove_inst_from_all"),  # 将乐器从所有房间中移除

    #  信息获取
    path('get_type/', views.get_type, name='get_type'),  # 获取所有的乐器类型信息
    path('get_inst/', views.get_inst, name='get_inst'),  # 获取所有的乐器信息
    path('get_room/', views.get_room, name='get_room'),  # 获取所有的房间信息

]
