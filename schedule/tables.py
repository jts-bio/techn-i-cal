from django.db.models import (Avg, Case, CharField, Count, F, FloatField,
                              IntegerField, Max, Min, OuterRef, Q, Sum, Value,
                              When)
from django_tables2 import tables
from django_tables2.utils import A
from django.utils.html import format_html

from sch.models import Employee, PtoRequest, Shift, ShiftTemplate, Slot, Workday, PtoRequest





class MistemplatedFlagIgnoreTable (tables.Table):

    slot =     tables.columns.Column(accessor='slug', orderable=False, verbose_name='UNDEFINED OR NO NAME')
    employee = tables.columns.Column(accessor=A('employee__name'))
    shift =    tables.columns.Column(accessor=A('shift'))
    # remove_ignore_button = tables.LinkColumn('schedule:unignore_mistemplate', text='Reflag')
    
    class Meta:
        model = Slot
        template_name = "django_tables2/bootstrap4.html"
        
        fields = ["slot", "employee", "shift"]

        empty_text = "No entries found. Check the admin table for more details."
    
    def render_slot(self, value, record):
        return "{msg} {slot}".format(msg=(
            '<span class="%s">(FLAGGED)</span>' % ('badge badge-danger') if record.flag else ""
        ), slot=record.slug)
    
    def render_employee(self, value, record):
        return record.employee
    
    def render_shift(self, value, record):
        return record.shift