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
from django.db import models


#  add <script src="https://unpkg.com/hyperscript.org"></script> the the base admin template
#  to enable the following:


class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'employee'


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
    fields = ['employee', 'shift', ]
    readonly_fields = ['employee', 'shift']
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ['shift__start']


class DeptEmployees(admin.StackedInline):
    model = Employee
    fields = ['name', 'fte', 'department', 'time_pref', 'streak_pref', 'shifts_trained', 'shifts_available']
    readonly_fields = ['department']
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ['fte','name']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(DeptEmployees, self).get_formset(request, obj, **kwargs)

        formset.form.base_fields['time_pref'].widget = forms.Select(choices=((('AM', 'Morning'),('PM', 'Evening'), ('XN', 'Overnight')))
        )
        # set choices to the Outer Department's shifts this StakedInline is in
        choices = obj.shifts.all()
        formset.form.base_fields['shifts_trained'] = forms.ModelMultipleChoiceField(
                                                                queryset=choices)
        formset.form.base_fields['shifts_available'] = forms.ModelMultipleChoiceField(
                                                                queryset=choices)
        formset.form.base_fields['fte'].widget = forms.NumberInput(attrs={'min': 0, 'max': 1, 'step': 0.125})
        # put up/down controls on the fte field
        formset.form.base_fields['fte'].widget.attrs['_'] = "on keyup[key='up'] if value < 1 increment value by 0.125 end "\
                                                            "on keyup[key='down'] if value > 0 increment value by -0.125 end"
        formset.form.base_fields['fte'].initial = 1
        return formset


class OrganizationDepartments(admin.StackedInline):
    model = Department
    fields = ['name', 'slug']
    readonly_fields = ['name', 'slug']
    extra = 0
    can_delete = True
    show_change_link = False
    ordering = ['name']


class ShiftsAvailable(admin.TabularInline):
    model = Employee.shifts_available.through
    fields = ['shift', 'employee']
    readonly_fields = ['shift', 'employee']
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ['shift__start']


# Unregister the provided model admin
admin.site.unregister(User)


# Register out own model admin, based on the default UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = [
        ("Personal info", {'fields': ['username', 'first_name', 'last_name', 'email', 'password']}),
    
        ("Permissions", {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),

        ("Important dates", {'fields': ['last_login', 'date_joined']}),
    ]
    readonly_fields = ['organization']
    inlines = [EmployeeInline,]
    
    def organization (self, obj):
        return obj.employee.department.organization.name if obj.employee else None


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):

    fieldsets = [
        ("Main", {'fields': ['name', ]}),
        ("Reference", {'fields': ['slug', ]}),
    ]
   
    list_display    = ['name', 'slug']
      
    inlines = [OrganizationDepartments,]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    fieldsets       = [
        ("Main", {'fields': ['name', 'slug', 'org']}),
        ("Options", {'fields': ['initial_start_date', 'schedule_week_length']}),
    ]
    list_display    = ['name', 'slug', 'org']
    inlines         = [DeptScheduleTable, DeptEmployees]


    def get_form(self, request, obj=None, **kwargs):
        form = super(DepartmentAdmin, self).get_form(request, obj, **kwargs)

        form.base_fields['schedule_week_length'].help_text = 'Number of Weeks per Schedule. ' \
                                                             'Start dates will be calculated every 7N days ' \
                                                             'from the initial start date.'
        return form



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
    list_filter     = ['department']
    ordering        = ['start']
    search_fields   = ['name', 'department__name', 'department__org__name']
    
    inlines = [EmployeesAvailable,]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    fieldsets         = [
        ('User', {'fields': ['user',]}),
        ('Main', {'fields':
                      ['name',
                       'initials',
                       'department',
                       'fte',
                       'cls',
                       'time_pref',
                       'streak_pref'],
                  }),
        ('Options', {'fields': ['std_wk_max']}),
        ]

    fte = forms.FloatField(widget=forms.NumberInput(attrs={'step': '0.125',
                                                           'min': '0',
                                                           'max': '1'}))
    fte.actions_on_bottom = True


    list_display = ['name', 'initials', 'fte','fte_14_day', 'streak_pref', 'cls', 'time_pref']
    
    inlines = [ShiftsAvailable, EmployeesTrained]

    group_by = ['department']


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


class EmployeeInlineSch(admin.TabularInline):
    model = Schedule.employees.through
    extra = 0
    can_delete = True
    show_change_link = True


@admin.register(Schedule)    
class ScheduleAdmin (admin.ModelAdmin):
    fields              = (
                            'department',
                            'slug',
                            'number', 
                            'year', 
                            'start_date', 
                            'data',
                            'employees'
                        )
    readonly_fields     = ('slug','start_date', 'percent', 'data', 'employees')
    list_display        = ('department', 'slug','start_date', 'percent',)

    inlines = [EmployeeInlineSch,]

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