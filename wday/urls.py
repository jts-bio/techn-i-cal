from django.urls import path
from . import views, api

app_name = 'wday'

urlpatterns = [
    path('', views.wdListView, name='wd-list'),
    path('<slug:slug>/', views.wdDetailView, name='wd-detail'),
    path('<slug:slug>/slot/<str:shiftId>/', views.slotDetailView, name='slot-detail'),
    path('<slug:slug>/slot/<str:shiftId>/delete/', views.SlotActions.slotDeleteView, name='slot-delete'),
    path('<slug:slug>/slot/<str:shiftId>/update/<str:empId>/', views.SlotActions.slotUpdateView, name='slot-update'),
    
    
    
    # API paths ~~~~~~~~~~~~~~~~~~~~~~
    path('<slug:wdSlug>/api/employee-can-fill/<slug:empSlug>/', api.empl_can_fill, name='slots--empl-can-fill')
    
]
