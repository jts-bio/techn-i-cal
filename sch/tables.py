from django.db.models import (Avg, Case, CharField, Count, F, FloatField,
                              IntegerField, Max, Min, OuterRef, Q, Sum, Value,
                              When)
from django_tables2 import tables
from django_tables2.utils import A
from django.utils.html import format_html

from .models import Employee, PtoRequest, Shift, ShiftTemplate, Slot, Workday, PtoRequest


class EmployeeTable (tables.Table):
    """
    Base Table for All Employees
    Displays basic details about each employee
    """
    name = tables.columns.LinkColumn('sch:v2-employee-detail', args=[A('name')])
    avg_shift_pref_score = tables.columns.Column(
        verbose_name="Avg Shift Pref Score", 
        accessor='avg_shift_pref_score')
    streak_pref = tables.columns.Column(
        verbose_name='Streak Preference', 
        accessor='streak_pref',
        attrs={'td':{'class':'text-center'}})
    templated_days = tables.columns.Column(
        verbose_name='Templated Days', 
        accessor='templated_days',
        attrs={'td':{'class':'text-center'}})
    templated_days_off = tables.columns.Column(
        verbose_name='Templated Days Off', 
        accessor='templated_days_off',
        attrs={'td':{'class':'text-center'}})

    class Meta:
        model           = Employee
        fields          = ['name', 'fte' ]
        template_name   = 'django_tables2/semantic.html'
        attrs           = { "class" : "table table-auto table-striped table-md min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-700"}
        sort_by         = ('name',)

    def render_fte(self, value):
        return f' {value:.3f}FTE '
    
    def render_avg_shift_pref_score(self, value):
        return f'{value:.0f}'
    
    def render_templated_days(self, record):
        return len(record.templated_days)
    
    def render_streak_pref(self,record):
        return "%s-in-a-row" % record.streak_pref
    
    def render_templated_days_off(self,record):
        return f'{" ".join([st.symb for st in record.templated_days_off])}'

class EmployeeWeeklyHoursTable (tables.Table):
    """
    Columns of Every (year,week) value...
    Rows of Each Employee
    """
    name = tables.columns.LinkColumn('employee-detail', args=[A('name')])
    
    class Meta:
        model           = Employee
        fields          = ['name',]
        template_name   = 'django_tables2/semantic.html'
        attrs           = {"class":"table table-compact table-xs"}
        sequence        = ('name',) # For header ordering

    def render_name(self, value):
        return str(value).upper()

class ShiftListTable (tables.Table) :
    """
    SHIFT LIST TABLE
        - Summary for ALL SHIFTS
    
    example 
    ---------------------------------------------------
    ```
    ---------------------------------
    name| hours   | IV?  | Group
    ---------------------------------
    MI  |  10 hrs |  X   |  CPhT
    RS  |  10 hrs |      |  RPh
    ---------------------------------
    ```
    """
    name  = tables.columns.LinkColumn    ("sch:shift-detail", args=[A("cls"),A("name")])
    hours = tables.columns.Column        (verbose_name="Hours", attrs={"td": {"class": "small text-xs"}})
    is_iv = tables.columns.BooleanColumn (verbose_name="IV Room?", attrs={"td":{"class":"text-center text-blue-900"}})
    on_days_display = tables.columns.Column(verbose_name="Scheduling Weekdays",attrs={"td":{"class":"text-center text-indigo-300"}})
    group = tables.columns.Column        (verbose_name="Time-of-Day Group", attrs={"td": {"class": "text-center", "style":"font-family:'Helvetica Neue';"}})
    
    class Meta:
        model           = Shift
        fields          = ['name','start','hours', 'is_iv','on_days_display',]
        template_name   = 'django_tables2/bootstrap.html'
        attrs           = { "class" : "table table-compact table-striped table-md min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-700"}
      
class ShiftsWorkdayTable (tables.Table):
    """View from a WORKDAY
    display ALL SHIFTS for a given day
    """
    del_slot = tables.columns.LinkColumn("slot-delete", args=[A("date"),A("pk")], verbose_name="Delete", attrs={"td": {"class": "small"}})
    class Meta:
        model           = Shift
        fields          = ['name','start','employee','del_slot']
        template_name   = 'django_tables2/bootstrap.html'

    def render_del_slot(self, record):
        return record.pk

class ShiftsWorkdaySmallTable (tables.Table):

    class Meta:
        model           = Shift
        fields          = [ 'name', 'employee' ]
        template_name   = 'django_tables2/bootstrap.html'
        
        attrs           = { "class" : "table table-compact table-striped table-md min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-700"}
        
    def render_employee(self, value, record):
        if record.cls == "RPh":
            return format_html("<span class='pharmer-gray {}'> {} <span class='xs'>{}</span></span>",record.employee.strip().replace(" ","-"), value, record.cls)
        elif record.cls == "CPhT":
            return format_html('<span class="tech-gray {}"> {} <span class="xs">{}</span></span>',record.employee.strip().replace(" ","-"), value, record.cls)

class WorkdayListTable (tables.Table):
    """Summary for ALL WORKDAYS
    """
    date       = tables.columns.LinkColumn("sch:v2-workday-detail", args=[A("slug")])
    n_unfilled = tables.columns.Column(verbose_name="Unfilled Shifts")
    days_away  = tables.columns.Column(verbose_name="Days Away")  


    class Meta:
        model           = Workday
        fields          = [
                            'date',         'iweek',        'iperiod',      'ischedule',    'sd_id',
                            'iweekday',     'n_unfilled',   'days_away',
                            'percFilled'
                           ]
        template_name   = 'django_tables2/bootstrap-responsive.html'
        attrs           = {"class":["rounded-lg w-full text-sm text-left text-gray-500 dark:text-gray-400","bg-white  dark:bg-gray-900"]}

    def render_n_unfilled(self, record):
        return record.n_unfilled

    def render_days_away(self, record):
        return f"in {record.days_away} days"
    
    def render_iweek(self, record):
        return f"W-{record.iweek}"
    
    def render_iperiod(self, record):
        return f"P-{record.iperiod}"
    
    def render_ischedule(self,record):
        return f'S-{record.ischedule}'
    
    def render_iweekday(self, record):
        WEEKDAY_CHOICES = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
        return WEEKDAY_CHOICES[record.iweekday]
    
    def render_date(self, record):
        return record.date.strftime("%d %b %Y")
    
    def render_percFilled(self, record):
        return f"{round(record.percFilled*100, 2)}%"
    
class WeekListTable (tables.Table):
    
    year              = tables.columns.Column()
    iweek             = tables.columns.Column()
    perc_filled       = tables.columns.Column (verbose_name="% Filled")
    
    class Meta:
        fields          = ['year','iweek','perc_filled']
        
    def render_week(self, record):
        return f"W{record.iweek}"
    
    def render_perc_filled (self,record):
        return f"{int(record['perc_filled']/104*100)}%"

    
class PtoListTable (tables.Table):

    class Meta:
        model           = PtoRequest
        fields          = ['workday', 'status', 'stands_respected' ]
        template_name   = 'django_tables2/bootstrap.html'

class WeeklyHoursTable (tables.Table):

    name  = tables.columns.LinkColumn("employee-detail", args=[A("name")])
    hours = tables.columns.Column(verbose_name="Weekly Hours")

    class Meta:
        model           = Employee
        fields          = ['name', 'hours']
        template_name   = 'django_tables2/bootstrap.html'

class PtoRequestTable (tables.Table):

    workday = tables.columns.LinkColumn("workday", args=[A("workday")])

    class Meta:
        model           = PtoRequest
        fields          = ['workday', 'status', 'stands_respected', 'employee', 'dateCreated', 'manager_approval' ]
        template_name   = 'django_tables2/bootstrap.html'
