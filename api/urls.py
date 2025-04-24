from django.urls import path
from . import views

urlpatterns = [
    path('flood/', views.get_flood, name='get_flood'),
    path('erosion/', views.get_erosion, name='get_erosion'),
    path('polygon/', views.get_polygon, name='get_polygon'),
    path('provinces/', views.get_all_provinces, name='get_all_provinces'),
    path('update-position/', views.update_position_province, name='update_position_province'),
    path('insert-user/', views.insert_user, name='insert_user'),
    path('add-disaster/', views.add_disaster_data, name='add_disaster_data'),
    path('update-disaster/', views.update_disaster_data, name='update_disaster_data'),
    path('delete-disaster/', views.delete_disaster_data, name='delete_disaster_data'),
]
