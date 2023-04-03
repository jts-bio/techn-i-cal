from django.urls import path
from . import views, api
from sch import components

app_name = 'wday'


urlpatterns = [
    
    path('', views.wdListView, name='wd-list'),
    path('<slug>/', views.wdDetailView, name='detail'),
    path('<slug>/slot/<shiftId>/', views.slotDetailView, name='slot-detail'),
    path('<wd>/delete/', views.WdActions.wdClearView, name='slot-delete'),
    path('<wd>/solve/', views.WdActions.wdSolveView, name='slot-solve'),
    path('<slug>/'+'slot/'+'<shiftId>/'+'update/',  views.SlotActions.slotUpdateView, name='slot-update'),

    # Components ~~~~~~~~~~~~~~~~~~~~~
    path('<wd>/partial/speed-dial/', views.Partials.speed_dial, name='speed-dial'),
    
    # API paths ~~~~~~~~~~~~~~~~~~~~~~
    path('<wdSlug>/api-context/', api.workday_context, name='workday-api-context'),
    
    path('testing/<wdSlug>/', views.testing, name='testing'),
    path('<wd>/<sft>/<empl>/assign/', views.SlotActions.slotAssignView, name='slot-assign'),
    path('<wd>/<sft>/clear/', views.SlotActions.slotClearView, name='slot-clear'),
    path('<wd>/<shift>/fill-template/', views.WdActions.fill_with_template, name='fill-template'),
    path('<wdSlug>/api/employee-can-fill/<empSlug>/', api.empl_can_fill, name='slots--empl-can-fill'),
    path('<wdSlug>/api/check-employee-surrounding/<empSlug>/', api.check_empl_surrounding, name='check-empl-surrounding'),
    path('<wdSlug>/api/empl-check-hours/<empSlug>/', api.empl_check_hours, name='empl-check-hours'),
    path('partial/<wdSlug>/spwd-breadcrumb/', views.Partials.spwdBreadcrumb, name='spwd-breadcrumb'),
    path('partial/<slotId>/slot-popover/', views.Partials.slotPopover, name='slot-popover'),
    path('api/tests/testing/example/eventViewTests/', views.Partials.events, name='events'),
]
