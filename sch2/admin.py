from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(Workday)
class WorkdayAdmin (admin.ModelAdmin):
    
    list_display = ('date', 'week', 'period', 'schedule', 'slug', 'iweekday', 'iweek', 'iperiod', 'ischedule', 'ppd_id', 'sd_id', )
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    
@admin.register(Employee)
class EmployeeAdmin (admin.ModelAdmin):
    
    list_display = ('initials', 'name', 'cls' , 'fte', 'hire_date', 'streak_pref', 'trade_one_offs', 'time_pref', )
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    
@admin.register(Shift)
class ShiftAdmin (admin.ModelAdmin):
    
    list_display = ('name', 'cls', 'duration', 'hours', 'group', )
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable =  ()