from django.urls import include, path, reverse
from . import views

app_name = 'empl'

urlpatterns = [

    path('', views.empl_list, name='list'),
    path('<empl>/shift-swaps/', views.empl_shift_swaps, name='shift-swaps'),
    path('new/', views.empl_new, name='new'),
    path('<empl>/profile-img-browser/', views.empl_profile_img_browser, name='img-chooser')
]

