from django.urls import path, include
from django.contrib import admin
from . import views


urlpatterns = [
    path('', views.index, name='index'),

    #? ==== Workday ==== ?#
    path('day/all/', views.WORKDAY.WorkdayListView.as_view(), name='workday-list'),
    path('day/<slug:slug>/', views.WORKDAY.WorkDayDetailView.as_view(), name='workday'),
    path('day/<slug:date>/fill-template/', views.workdayFillTemplate, name='workdayFillTemplate'),
    path('days/new/', views.WORKDAY.WorkdayBulkCreateView.as_view(), name='workday-new'),

    #? ==== Week ==== ?#
    path('week/<int:year>/<int:week>/', views.WEEK.WeekView.as_view(), name='week'),
    path('week/<int:year>/<int:week>/fill-template/', views.WEEK.weekFillTemplates, name='weekFillTemplate'),

    #? ==== Slots ==== ?#
    path('day/<slug:date>/<str:shift>/new/', views.SLOT.SlotCreateView.as_view(), name='slot-new'),
    path('day/<slug:date>/<str:shift>/add/', views.slotAdd, name='slot-add'),
    path('day/<slug:date>/<str:shift>/add/post', views.slotAdd_post, name='slot-add-post'),  # type: ignore
    path('day/<slug:date>/<str:shift>/delete/', views.SLOT.SlotDeleteView.as_view(), name='slot-delete'),
    path('day/<slug:date>/<str:employee>/resolve-pto-request/', views.WORKDAY.ResolvePtoRequestFormView.as_view(), name='resolve-pto-request'),

    #? ==== Shifts ==== ?#
    path('shifts/all/', views.SHIFT.ShiftListView.as_view(), name='shift-list'),
    path('shift/<str:name>/', views.SHIFT.ShiftDetailView.as_view() , name='shift'),
    path('shift/<str:name>/update/', views.SHIFT.ShiftUpdateView.as_view(), name='shift-update'),
    path('shifts/new/', views.SHIFT.ShiftCreateView.as_view(), name='shift-new'),
    path('shift/<str:shift>/template/', views.shiftTemplate, name='shift-template'),

    #? ==== Employees ==== ?#
    path("employees/all/", views.EMPLOYEE.EmployeeListView.as_view(), name='employee-list'),
    path("employees/new/", views.EMPLOYEE.EmployeeCreateView.as_view(), name='employee-new'),
    path('employee/<str:name>/', views.EMPLOYEE.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employee/<str:name>/update/', views.EMPLOYEE.EmployeeUpdateView.as_view(), name='employee-update'),
    path('employee/<str:name>/ssts/', views.EmpSSTView, name='employee-edit-ssts'),   
    path('employee/<str:name>/pto-request/add/', views.EMPLOYEE.EmployeeAddPtoView.as_view(), name='employee-add-pto'),
    path('employee/<str:name>/pto-request/add-range/', views.EMPLOYEE.EmployeeAddPtoRangeView.as_view(), name='employee-add-pto-range'),
<<<<<<< HEAD
    path('employee/<str:name>/generate-schedule', views.EMPLOYEE.EmployeeScheduleFormView.as_view(), name='employee-schedule-form'),
    path('employee/<str:name>/generate-schedule/<slug:date_from>/<slug:date_to>', views.EMPLOYEE.EmployeeScheduleView.as_view(), name='employee-schedule'),  # type: ignore
=======
    path('employee/<str:name>/generate-schedule/', views.EMPLOYEE.EmployeeScheduleFormView.as_view(), name='employee-schedule-form'),
    path('employee/<str:name>/generate-schedule/<slug:date_from>/<slug:date_to>/', views.EMPLOYEE.EmployeeScheduleView.as_view(), name='employee-schedule'),  # type: ignore
>>>>>>> 9d70c33 (edit - Who Can Fill Filters working well)

    #? ==== PTO Requests ==== ?#
    
]
