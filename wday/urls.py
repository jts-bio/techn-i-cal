from django.urls import path
from . import views, api

app_name = 'wday'

urlpatterns = [
    path('', views.wdListView, name='wd-list'),
    path('<slug>/', views.wdDetailView, name='detail'),
    path('<slug>/slot/<shiftId>/', views.slotDetailView, name='slot-detail'),
    path('<slug>/slot/<shiftId>/delete/', views.SlotActions.slotDeleteView, name='slot-delete'),
    path('<slug>/slot/<shiftId>/update/<empId>/', views.SlotActions.slotUpdateView, name='slot-update'),
    
    # API paths ~~~~~~~~~~~~~~~~~~~~~~
    path('<wdSlug>/api/employee-can-fill/<empSlug>/', api.empl_can_fill, name='slots--empl-can-fill'),
    path('partial/<wdSlug>/spwd-breadcrumb/', views.Partials.spwdBreadcrumb, name='spwd-breadcrumb'),
    path('partial/<slotId>/slot-popover/', views.Partials.slotPopover, name='slot-popover'),
    path('api/tests/testing/example/eventViewTests/', views.Partials.events, name='events'),
]
