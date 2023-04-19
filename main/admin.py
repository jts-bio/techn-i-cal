from django.contrib import admin
from .models import * 


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)
   
@admin.register(Department) 
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
   
@admin.register(Employee) 
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name',)
  
@admin.register(Shift)  
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'hours')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    
@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ('name',)