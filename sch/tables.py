from django_tables2 import tables
from django_tables2.utils import A

from .models import Shift, Employee, Workday, Slot, ShiftTemplate
from django.db.models import Q, F, Count, Sum, Max, Min, Avg, FloatField, IntegerField, Case, When, Value, CharField, OuterRef




class EmployeeTable (tables.Table) :

    name = tables.columns.LinkColumn('employee_detail', args=[A('name')])

    class Meta:
        model           = Employee
        fields          = ['name','shifts_trained', 'shifts_available']
        template_name   = 'django_tables2/bootstrap.html'

class ShiftListTable (tables.Table) :

    name = tables.columns.LinkColumn("shift", args=[A("name")])
    class Meta:
        model           = Shift
        fields          = ['name','start', 'end','duration', 'occur_days']
        template_name   = 'django_tables2/bootstrap.html'
        
class ShiftsWorkdayTable (tables.Table) :
    class Meta:
        model           = Shift
        fields          = ['name','start','employee']
        template_name   = 'django_tables2/bootstrap.html'

class WorkdayListTable (tables.Table):

    date = tables.columns.LinkColumn("workday", args=[A("date")])
    class Meta:
        model           = Workday
        fields          = ['date', 'iweek', 'iperiod', 'iweekday', 'date__year']
        template_name   = 'django_tables2/bootstrap.html'
    

