from django.urls import include, path

from . import views

app_name = "rosbags"
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_view, name='list'),
    path('bag/<path:bag_path>/', views.detail, name='detail'),
    path('bag/<path:bag_path>/thumbnail/<str:thumb_name>', views.thumbnail, name='thumbnail'),
    path('api/generate_thumbnails', views.generate_thumbnails, name='generate_thumbnails')
]
