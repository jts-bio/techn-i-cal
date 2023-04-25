from django.urls import include, path, reverse
from . import views

app_name = 'empl'

urlpatterns = [
    
    path('<empid>/shift-swaps/', views.empl_shift_swaps, name='shift-swaps'),

]

