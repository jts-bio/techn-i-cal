
# serializers.py
from rest_framework import serializers
from .models import Employee, Workday, Shift, Slot, ShiftTemplate, TemplatedDayOff, Workday, Week, Period, Schedule, ShiftSortPreference, PtoRequest

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('name', 'fte_14_day', 'fte', 'shifts_trained',
                  'shifts_available','trade_one_offs', 'cls', 'time_pref', 'slug')
        
class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ('employee', 'slot', 'shift_template', 'week', 'period', 'schedule', 'slug')
        
class WorkdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Workday
        fields = ('date', 'week', 'period', 'schedule', 'slug', 'iweekday', 'iweek','iperiod','ischedule','ppd_id','sd_id')
        
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
        fields = ('slug', 'start_date', 'number', 'year','version')
        
class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ('workday','shift','employee','week','period','schedule','is_terminal','is_turnaround','streak','template_employee')
        
class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = ('shift','employee','sd_id')
                
class TemplatedDayOff (serializers.ModelSerializer):
    class Meta:
        model = TemplatedDayOff
        fields = ('employee','sd_id')
        
class PtoRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PtoRequest
        fields = ('employee','start_date','end_date','status','request_type','requester','reason','slug')
            
        


# views.py
from rest_framework import viewsets
from .models import Article
from .serializers import ArticleSerializer

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

# urls.py
from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'articles', views.ArticleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

