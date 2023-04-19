from django.contrib import admin
from .models import * 


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
        'organization',
        'schedule_week_count',
        'schedule_period_count',
        'schedule_start_date'
    ]
    list_display = ('name',)
   
@admin.register(Employee) 
class EmployeeAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'department',
        'initials',
        'hire_date',
        'active'
    ]
    list_display = ('name',)
  
@admin.register(Shift)  
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'hours')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    fields = [
        'start_date',
        'year',
        'number',
        'published',
        'department',
        'published_version'
    ]
    list_display = ('start_date',)
    
@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ('name',)