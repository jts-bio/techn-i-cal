from django.contrib import admin

# Register your models here.
from .models import (
    Shift, Employee, TemplatedDayOff, Workday, Slot, 
    ShiftTemplate, PtoRequest, Week, Period, Schedule

)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    fields          = ['name', 'start','duration','occur_days',]
    list_display    = ['name','start','duration','occur_days',]

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    fields          = ['name','fte_14_day','fte','streak_pref','shifts_trained','shifts_available','trade_one_offs', 'cls','time_pref']
    readonly_fields = ['fte']
    list_display    = ['name', 'fte_14_day', 'streak_pref','cls','time_pref']

@admin.register(Workday)
class WorkdayAdmin(admin.ModelAdmin):
    fields          = ['date', 'iweekday','iweek','iperiod','ppd_id','slug','shifts',]
    readonly_fields = ['iweekday','iweek', 'iperiod','ppd_id','slug','shifts',]
    list_display    = ['date','iweekday','iweek','iperiod','ppd_id','slug',]

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    fields          = ['workday', 'shift','employee','start','slug',]
    readonly_fields = ['start','slug',]
    list_display    = ['workday','shift','employee','start','slug',]

@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    fields          = ['shift','employee','sd_id']
    list_display    = ['shift','employee','sd_id']

@admin.register(PtoRequest)
class PtoRequestAdmin(admin.ModelAdmin):
    fields          = ['workday','employee','status','stands_respected',]
    readonly_fields = ['stands_respected',]
    list_display    = ['workday','employee','status','stands_respected',]

@admin.register(TemplatedDayOff)
class TmplDayOffAdmin(admin.ModelAdmin):
    fields          = ['employee', 'sd_id']
    list_display    = ['employee', 'sd_id']
    
@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    fields = ('year', 'number', 'period', 'schedule', 'start_date', )
    list_display = ('year', 'number', 'period', 'schedule', 'start_date', )