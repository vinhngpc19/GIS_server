from django.urls import path
from . import views

urlpatterns = [
    path('flood', views.getFlood),
    path('polygon', views.getPolygon),
    path('all_provinces', views.getAllProvinces),
]
