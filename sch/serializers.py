# serializers.py

from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)
from rest_framework import serializers
from .models import (Employee, Workday, Shift, Slot, ShiftTemplate, 
                     TemplatedDayOff, Workday, Week, Period, 
                     Schedule, ShiftSortPreference, PtoRequest )



class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('__all__')
        
class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ('__all__')
        
class WorkdaySerializer(serializers.ModelSerializer):
    
    url = serializers.SerializerMethodField()
    
    def get_url (self, obj):
        return f'/wday/{obj.slug}/'
    
    class Meta:
        model = Workday
        fields = ('__all__')
        
class WeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Week
        fields = ('__all__')
        
class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ('__all__')
        
class ScheduleSerializer(TaggitSerializer, serializers.ModelSerializer):
    
    slots       = serializers.StringRelatedField(many=True)
    clear_url   = serializers.SerializerMethodField()
    tags        = TagListSerializerField()
    
    def get_clear_url(self, obj):
        return f'/schedule/detail/{obj.slug}/actions/clear-all/'
    
    class Meta:
        model = Schedule
        fields = ('__all__')
        
class SlotSerializer(serializers.ModelSerializer):
    
    employee= serializers.StringRelatedField()
    workday = serializers.StringRelatedField()
    weekday = serializers.SerializerMethodField()
    shift   = serializers.StringRelatedField()
    clear_url    = serializers.SerializerMethodField()
    workday_url  = serializers.SerializerMethodField()
    
    
    def get_clear_url(self, obj):
        return f'/schedule/detail/{obj.schedule.slug}/actions/clear-slot/{obj.workday.slug}/{obj.shift.name}/'
    
    def get_workday_url (self, obj):
        return f'/wday/{obj.workday.slug}/'
    
    def get_weekday (self, obj):
        return obj.workday.weekday
    
    class Meta:
        model = Slot
        fields = ('__all__')
        
class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = ('__all__')
                
class TemplatedDayOffSerializer (serializers.ModelSerializer):
    class Meta:
        model = TemplatedDayOff
        fields = ('employee','sd_id')
        
class PtoRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PtoRequest
        fields = ('__all__')
            
class ShiftSortPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSortPreference
        fields = ('__all__')

