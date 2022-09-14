from django.urls import path, include
from django.contrib import admin
from . import views


urlpatterns = [
    path('', views.index, name='index'),

    #? ==== Workday ==== ?#
    path('day/<slug:slug>/', views.WorkDayDetailView.as_view(), name='workday'),
    path('day/<slug:date>/fill-template/', views.workdayFillTemplate, name='workdayFillTemplate'),

    #? ==== Week ==== ?#
    path('week/<int:year>/<int:week>/', views.weekView, name='week'),

    #? ==== Slots ==== ?#
    path('day/<slug:date>/<str:shift>/', views.slot, name='slot'),
    path('day/<slug:date>/<str:shift>/add/', views.slotAdd, name='slot-add'),
    path('day/<slug:date>/<str:shift>/add/post', views.slotAdd_post, name='slot-add-post'),
    path('day/<slug:date>/<str:shift>/delete/', views.slotDelete, name='slot-delete'),

    #? ==== Shifts ==== ?#
    path('shift/<str:shift>/', views.shift, name='shift'),
    path('shift/<str:shift>/template/', views.shiftTemplate, name='shift-template'),

    #? ==== Employees ==== ?#
    path('employee/<str:name>/', views.EmployeeDetailView.as_view(), name='employee'),
]
