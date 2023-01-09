
# serializers.py
from rest_framework import serializers
from .models import Employee, Workday, Shift, Slot, ShiftTemplate, TemplatedDayOff, Workday, Week, Period, Schedule, ShiftSortPreference, PtoRequest

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('__all__')
        
class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ('employee', 'slot', 'shift_template', 'week', 'period', 'schedule', 'slug')
        
class WorkdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Workday
        fields = ('__all__')
        
class WeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Week
        fields = ('start_date', 'number', 'year','period', 'version')
        
class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ('start_date', 'number', 'year','schedule','version')
        
class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ('__all__')
        
class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ('__all__')
        
class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = ('shift','employee','sd_id')
                
class TemplatedDayOffSerializer (serializers.ModelSerializer):
    class Meta:
        model = TemplatedDayOff
        fields = ('employee','sd_id')
        
class PtoRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PtoRequest
        fields = ('__all__')
            
        

