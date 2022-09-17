from django_tables2 import tables

from .models import Shift, Employee, Workday, Slot, ShiftTemplate
from django.db.models import Q, F, Count, Sum, Max, Min, Avg, FloatField, IntegerField, Case, When, Value, CharField, OuterRef




class EmployeeTable (tables.Table) :

    link = tables.columnURL('sch:employee_edit', args=[tables.A('pk')], text='Edit', attrs={'class': 'btn btn-primary btn-sm'})

    class Meta:
        model = Employee
        fields = ['name','shifts_trained', 'shifts_available']
        attrs = {"class": "table table-striped table-hover"}
