from django.contrib import admin
from .models import * 


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fields = [
        'user',
        'organization',
        'admin'
    ]
    list_display = ('user', 'organization', 'admin')

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    fields = [
        'name',
    ]
    list_display = ('name',)
   
@admin.register(Department) 
class DepartmentAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'slug',
        'organization',
        'schedule_week_count',
        'schedule_start_date_init'
    ]
    readonly_fields = ['shifts']
    list_display = (
        'name',
        'slug',
        'organization',
        'schedule_week_count',
        'schedule_start_date_init'
    )
   
@admin.register(Employee) 
class EmployeeAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'slug',
        'department',
        'initials',
        'hire_date',
        'active',
        'fte',
        'shifts_trained',
        'shifts_available',
        'std_weekly_hours'
    ]
    list_display = (
        'name',
        'pk', 
        'fte', 
        'active', 
        'department',
        'std_weekly_hours'
    )
  
@admin.register(Shift)  
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'hours', 'phase', 'weekdays', 'department')
    fields = [
        'name',
        'slug',
        'department',
        'weekdays',
        'hours',
        'phase',
        'on_holidays',
    ]

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    fields = [
        'start_date',
        'year',
        'number',
        'published',
        'department',
    ]
    list_display = ('start_date','number','department')
    # group list by dept.
    list_filter = ('department',)
    
@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ('name','schedule','status','department','n_workdays','n_slots')
    fields = [
        'name',
        'schedule',
        'status',
        
    ]
    list_filter = ('schedule','status')

    def department(self, obj):
        return obj.schedule.department
    
    def n_workdays(self, obj):
        return obj.workdays.count()
    
    def n_slots(self, obj):
        return Slot.objects.filter(workday__version=obj).count()

@admin.register(Workday)
class WorkdayAdmin(admin.ModelAdmin):
    list_display = ('date','version','n_slots','sdid','wkid','pdid')
    fields = [
        'date',
        'version',
    ]
    list_filter = ('version','date')

    def n_slots(self, obj):
        return obj.slots.count()

@admin.register(DayOffMap)
class DayOffMapAdmin(admin.ModelAdmin):
    list_display = ('employee','days_off')
    fields = [
        'employee',
        'days_off',
    ]

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('workday','shift','employee')
    fields = [
        'workday',
        'shift',
        'employee',
        'fills_with',
    ]
    readonly_fields = [
        'fills_with'
    ]
    list_filter = ('workday','shift','employee',)