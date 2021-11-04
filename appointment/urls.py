from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name = 'index'),
    #path('manage/inst/', views.inst, name = 'manage_inst'),
    #path('manage/room/', views.room, name = 'manage_room'),
    path('manage/type/', views.type, name = 'manage_type'),
    path('get_type/', views.get_type, name = 'get_type')
]