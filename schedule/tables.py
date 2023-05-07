from django.db.models import (
        Avg, Case, CharField, Count, F, FloatField,
        IntegerField, Max, Min, OuterRef, 
        Q, Sum, Value, When 
    )
from django_tables2 import tables
from django_tables2.utils import A
from django.utils.html import format_html

from sch.models import (
        Employee, PtoRequest, Shift, 
        ShiftTemplate, Slot, Workday, 
        PtoRequest, Schedule
    )





class MistemplatedFlagIgnoreTable (tables.Table):

    slot =     tables.columns.Column(accessor='slug', orderable=False, verbose_name='UNDEFINED OR NO NAME')
    employee = tables.columns.Column(accessor=A('employee__name'))
    shift =    tables.columns.Column(accessor=A('shift'))
    # remove_ignore_button = tables.LinkColumn('schedule:unignore_mistemplate', text='Reflag')
    
    class Meta:
        model = Slot
        template_name = "django_tables2/bootstrap4.html"
        empty_text = "No entries found. Check the admin table for more details."

        fields = [
            "slot", 
            "employee", 
            "shift"
            ]

    def render_slot(self, value, record):
        return "{msg} {slot}".format(msg=(
            '<span class="%s">(FLAGGED)</span>' % ('badge badge-danger') if record.flag else ""
        ), slot=record.slug)
    
    def render_employee(self, value, record):
        return record.employee
    
    def render_shift(self, value, record):
        return record.shift
    
    

class TdoConflictsTable (tables.Table):
    
    shift =     tables.columns.Column(accessor='shift', orderable=False, verbose_name='Shift')
    workday =   tables.columns.Column(accessor='workday', orderable=False, verbose_name='Workday')
    employee =  tables.columns.Column(accessor=A('employee__name'))
    actions =   tables.columns.Column(accessor='employee__name', orderable=False, verbose_name='Actions')
    
    class Meta:
        model = Slot
        fields = [
        
            "employee",
            "actions"
        ]
        
    def render_actions (self, value, record):
        view_btn = format_html(
            '<a class="btn btn-sm bg-amber-400" href="{}">View</a>', 
            record.url())
        
        del_btn = format_html(
            '<div class="btn btn-sm bg-red-600" hx-post="{}">Delete</a>', 
            f"actions/clear-slot/{record.workday.slug}/{record.shift.name}/")
        
        return format_html("{} {}", view_btn, del_btn)



class ScheduleComparisonTable (tables.Table):

    pto_requests  = tables.columns.Column(accessor='pto_requests__all__count', orderable=False, verbose_name='# PTO Requests')
    pto_conflicts = tables.columns.Column(accessor='pto_conflicts__count', orderable=False, verbose_name='# PTO Conflicts')
    tdo_conflicts = tables.columns.Column(accessor='tdo_conflicts__count', orderable=False, verbose_name='# TDO Conflicts')

    class Meta:
        model = Schedule
        template_name = "django_tables2/bootstrap4.html"

        
        fields = [
            "slug", 
            "start_date", 
            "status",  
            "percent",
            ]

        empty_text = "No entries found. Check the admin table for more details."