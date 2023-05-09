from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import (
                Organization, Department,
                Shift, Employee, TemplatedDayOff, Workday, Slot, 
                ShiftTemplate, PtoRequest, Week, Period, Schedule,
                RoutineLog, LogEvent, WorkdayViewPreference, Turnaround )

from .forms import ShiftAvailableEmployeesForm
from django import forms


class DeptScheduleTable(admin.TabularInline):
    model = Schedule
    fields = ['slug', 'start_date', 'percent']
    readonly_fields = []
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ['-start_date']
    
class EmployeesAvailable(admin.TabularInline):
    model = Employee.shifts_available.through
    fields = ['employee', 'shift']
    readonly_fields = ['employee', 'shift']
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ['shift__start']
    
class EmployeesTrained(admin.TabularInline):
    model = Employee.shifts_trained.through
    fields = ['employee', 'shift']
    readonly_fields = ['employee', 'shift']
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ['shift__start']
    
class DeptEmployees(admin.TabularInline):
    model = Employee
    fields = ['name', 'fte', 'fte_14_day', 'cls', 'time_pref', 'streak_pref']
    readonly_fields = ['name', 'fte', 'fte_14_day', 'cls', 'time_pref', 'streak_pref']
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ['name']    

class OrganizationDepartments(admin.TabularInline):
    model = Department
    fields = ['name', 'slug']
    readonly_fields = ['name', 'slug']
    extra = 0
    can_delete = True
    show_change_link = False
    ordering = ['name']


# Unregister the provided model admin
admin.site.unregister(User)

# Register out own model admin, based on the default UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = [
        ("Personal info", {'fields': ['username', 'first_name', 'last_name', 'email', 'password']}),
        ("Organization", {'fields': ['employee', 'organization']}),
        ("Permissions", {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ("Important dates", {'fields': ['last_login', 'date_joined']}),
    ]
    
    readonly_fields = ['organization']
    
    def organization(self, obj):
        return obj.employee.organization.name if obj.employee else None

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):

    fieldsets = [
        ("Main", {'fields': ['name', ]}),
        ("Reference", {'fields': ['slug', ]}),
        ("Inlines", {'fields': []}),
    ]
   
    list_display    = ['name', 'slug']
      
    inlines = [OrganizationDepartments,]
    
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    fields          = ['name', 'slug', 'org']
    list_display    = ['name', 'slug', 'org']
    inlines         = [DeptScheduleTable, DeptEmployees]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    fields          = [
                'name', 
                'start',
                'duration',
                'occur_days',
                'coverage_for',
                'department'
            ]
    list_display    = [
                'name', 
                'start',
                'duration',
                'occur_days',
                'display_coverage_for',
                'department'
            ]
    
    inlines = [EmployeesAvailable,]
    


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    fields          = [
                'name',
                'initials',
                'user',
                'fte_14_day',
                'fte', 
                'department',
                'streak_pref',
                'shifts_trained', 
                'shifts_available',
                'trade_one_offs', 
                'cls', 
                'time_pref',
                'pto_hrs'
            ]
    list_display = ['name', 'initials', 'fte','fte_14_day', 'streak_pref', 'cls', 'time_pref']
    
    shifts_available = forms.ModelMultipleChoiceField(
        queryset=Shift.objects.all(),
        required=False,
        widget=forms.widgets.CheckboxSelectMultiple(
            attrs={'class': 'grid-cols-3'}
        ))
    

    

@admin.register(Workday)
class WorkdayAdmin(admin.ModelAdmin):
    fields          = [
                        'date', 
                        'iweekday',
                        'iweek',
                        'iperiod',
                        'ppd_id',
                        'slug',
                        'shifts',
                    ]
    readonly_fields = ['iweekday','iweek', 'iperiod','ppd_id','slug','shifts',]
    list_display    = ['date','iweekday','iweek','iperiod','ppd_id','slug',]
    
@admin.register(Turnaround)
class TurnaroundAdmin(admin.ModelAdmin):
    fields          = ['schedule','employee','early_slot', 'late_slot']
    list_display    = ['schedule','employee','date']
    
    def date(self, obj):
        return obj.early_slot.workday.date

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    fields          = ['workday', 'shift','employee','  start', 'slug','fills_with']
    readonly_fields = ['start',   'slug', 'fills_with', 'streak']
    list_display    = ['workday', 'shift','employee',  'start', 'slug','streak' ]

@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    fields          = ['shift','employee','sd_id']
    list_display    = ['shift','employee','sd_id']

@admin.register(PtoRequest)
class PtoRequestAdmin(admin.ModelAdmin):
    fields          = ['workday','employee','status','stands_respected',]
    readonly_fields = ['stands_respected',]
    list_display    = ['workday','employee','status','stands_respected',]
    
   
    list_filter     = ['status','employee']

@admin.register(TemplatedDayOff)
class TmplDayOffAdmin(admin.ModelAdmin):
    fields          = ['employee', 'sd_id']
    list_display    = ['employee', 'sd_id']
    
@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    fields          = ('year', 'number', 'period', 'schedule', 'start_date', 'hours' )
    list_display    = ('year', 'number', 'period', 'schedule', 'start_date', )

@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    fields          = (
                        'number',
                        'year', 
                        'schedule', 
                        'start_date', 
                        'hours' 
                    )
    list_display    = ('number','year','schedule', 'start_date', 'hours' )
    
@admin.register(Schedule)    
class ScheduleAdmin (admin.ModelAdmin):
    fields              = (
                            'department',
                            'slug',
                            'number', 
                            'year', 
                            'start_date', 
                            'data',
                        )
    readonly_fields     = ('slug','start_date', 'percent', 'data', )
    list_display        = ('department', 'slug','start_date', 'percent',)


    def pto_requests(self, obj):
        return obj.pto_requests.count()
    
    def pto_conflicts(self, obj):
        return obj.pto_requests.filter(stands_respected=False).count()


@admin.register(RoutineLog)
class RoutineLogAdmin (admin.ModelAdmin):
    fields          = ['schedule']
    list_display    = ['schedule']
    
@admin.register(LogEvent)
class LogEventAdmin (admin.ModelAdmin):
    fields          = ('log', 'event_type', 'description')
    list_display    = ('log', 'event_type', 'description')
    
@admin.register(WorkdayViewPreference)
class WorkdayViewPreferenceAdmin (admin.ModelAdmin):
    fields          = ('user', 'view')
    list_display    = ('user', 'view')