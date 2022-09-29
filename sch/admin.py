from django.contrib import admin

# Register your models here.
from .models import (
    Shift, Employee, Workday, Slot, 
    ShiftTemplate, PtoRequest, Photo
)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    fields          = ['name', 'start','duration','occur_days',]
    list_display    = ['name','start','duration','occur_days',]

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    fields          = ['name','fte_14_day','streak_pref','shifts_trained','shifts_available',]
    list_display    = ['name', 'fte_14_day', 'streak_pref',]

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
    fields          = ['shift','employee','ppd_id',]
    list_display    = ['shift','employee','ppd_id',]

@admin.register(PtoRequest)
class PtoRequestAdmin(admin.ModelAdmin):
    fields          = ['workday','employee','status','stands_respected',]
    readonly_fields = ['stands_respected',]
    list_display    = ['workday','employee','status','stands_respected',]

@admin.register(Photo)
class PhotoRequestAdmin(admin.ModelAdmin):
    fields          = ['photo']