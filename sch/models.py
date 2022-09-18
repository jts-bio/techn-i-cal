"--- MODELS.py ---"

from django.db import models
from django.urls import reverse
from django.db.models import Q, F, Count, Sum, Max, Min, Avg, StdDev, Variance, QuerySet
from computedfields.models import ComputedFieldsModel, computed
from multiselectfield import MultiSelectField
import datetime as dt

DAYCHOICES = (
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday')
    )
WEEKABCHOICES = (
        (0, 'A'),
        (1, 'B'),)

#* Managers
# ============================================================================
class ShiftManager (models.QuerySet):

    def on_weekday (self, weekday) -> QuerySet:
        return self.filter(occur_days__contains=weekday)

    def on_workday (self, workday):
        return self.filter(occur_days=workday.iweekday)

    def to_fill (self,workday):
        slot_exits = Slot.objects.filter(workday=workday).values_list('shift',flat=True)
        return self.exclude(name__in=slot_exits)

    def empl_is_trained (self, employee):
        empl = Employee.objects.get(name=employee)
        return self.filter(name__in=empl.shifts_trained.all())

# ============================================================================
class SlotManager (models.QuerySet):

    def on_workday (self, workday):
        return self.filter(workday=workday)

    def ShiftDetail (self, workday, shift):
        if self.filter(workday=workday, shift=shift).exists():
            return self.filter(workday=workday, shift=shift).annotate(
                employee= F('employee__name'),workday= F('workday__date')
                )
        else:
            return self.filter(workday=workday, shift=shift).annotate(
                employee= None, workday= F('workday__date')
                )

# ============================================================================
class EmployeeManager (models.QuerySet):

    def trained_for (self,shift):
        return self.filter(shifts_trained=shift)

    def in_slot (self, shift, workday):
        return self.filter(slot__shift__name=shift, slot__workday=workday)

# ============================================================================  
class WorkdayManager (models.QuerySet):
    def in_week(self, year, iweek):
        return self.filter(date__year=year, iweek=iweek)

    def same_week (self, workday):
        week = workday.iweek
        year = workday.date.year
        return self.filter(iweek=week, date__year=year)

#* Models
# ============================================================================
class Shift (models.Model) :
    # fields: name, start, duration 
    name        = models.CharField(max_length=100)
    start       = models.TimeField()
    duration    = models.DurationField()
    occur_days  = MultiSelectField(choices=DAYCHOICES, max_choices=7, max_length=14, default=[0,1,2,3,4,5,6])

    def __str__(self) :
        return self.name

    def url(self):
        return reverse("shift", kwargs={"name": self.name})

    @property
    def ppd_ids(self):
        """
        Returns a list of the ids of the PPDs (0-13) that this shift occurs on.
        """
        ids = list(self.occur_days)
        for i in self.occur_days:
            ids.append(str(int(i)+7))
        return ids

    @property
    def end (self):
        return (dt.datetime(2022,1,1,self.start.hour,self.start.minute) + self.duration).time()


    def trained_employees (self):
        return Employee.objects.filter(shifts_trained=self)

    objects = ShiftManager.as_manager()

# ============================================================================
class Employee (ComputedFieldsModel) :
    # fields: name, fte_14_day , shifts_trained, shifts_available 
    name            = models.CharField(max_length=100)
    fte_14_day      = models.FloatField()
    shifts_trained  = models.ManyToManyField(Shift, related_name='trained')
    shifts_available= models.ManyToManyField(Shift, related_name='available')
    streak_pref     = models.IntegerField(default=3)

    def __str__(self) :
        return self.name
    # computed fields:

    @computed(models.FloatField(), depends=[('self',['fte_14_day'])])
    def fte (self):
        return self.fte_14_day / 80

    def url(self):
        return reverse("employee", kwargs={"name": self.name})

    def trained_for (self, shift):
        return Shift.objects.filter(name__in=self.shifts_trained.all())

    def available_for (self, shift):
        return Shift.objects.filter(name__in=self.shifts_available.all())

    objects = EmployeeManager.as_manager()

# ============================================================================
class Workday (ComputedFieldsModel) :
    # fields: date, shifts 
    date = models.DateField()

    @computed(models.SlugField(max_length=20), depends=[('self',['date'])])
    def slug (self) -> str: 
        return self.date.strftime('%Y-%m-%d')

    @computed(models.IntegerField(), depends=[('self',['date'])])
    def iweekday (self) -> int:
        # range 0 -> 6
        return int (self.date.strftime('%w'))
    
    @computed(models.IntegerField(), depends=[('self',['date'])])
    def iweek (self) -> int:
        # range 0 -> 53
        return int (self.date.strftime('%U'))
    
    @computed(models.IntegerField(), depends=[('self',['date'])])
    def iperiod (self) -> int:
        # range 0 -> 27
        return int (self.date.strftime('%U')) // 2

    @computed(models.IntegerField(), depends=[('self',['date'])])
    def ppd_id (self) -> int:
        # range 0 -> 13
        return (self.date - dt.date(2022,9,4)).days % 14
    
    def weekday (self) -> str :
        # Sun -> Sat
        return self.date.strftime('%a')
    
    @computed(models.ManyToManyField(Shift), depends=[('self',['date'])])
    def shifts (self) -> ShiftManager:
        print (Shift.objects.all().first().values('occur_days')) # type: ignore
        return Shift.objects.filter(occur_days__contains= self.iweekday)  # type: ignore

    def siblings_iweek (self) -> "WorkdayManager":
        return Workday.objects.same_week(self) # type: ignore

    def __str__(self) :
        return str(self.date.strftime('%Y %m %d'))

    def url(self) -> str:
        return reverse("workday", kwargs={"slug": self.slug})
    
    def prevWD(self) -> "Workday":
        try:
            return Workday.objects.get(date=self.date - dt.timedelta(days=1))
        except Workday.DoesNotExist:
            return self

    def nextWD(self) -> "Workday":
        try:
            return Workday.objects.get(date=self.date + dt.timedelta(days=1))
        except Workday.DoesNotExist:
            return self
    
    def prevURL (self) -> str:
        return reverse("workday", kwargs={"slug": (self.date - dt.timedelta(days=1)).strftime('%Y-%m-%d')})

    def nextURL (self) -> str:
        return reverse("workday", kwargs={"slug": (self.date + dt.timedelta(days=1)).strftime('%Y-%m-%d')})

    @property
    def daysAway (self) -> int:
        return (self.date - dt.date.today()).days
    
    objects = WorkdayManager.as_manager()

# ============================================================================
class Slot (ComputedFieldsModel) :
    # fields: workday, shift, employee
    workday  = models.ForeignKey(Workday,  on_delete=models.CASCADE)
    shift    = models.ForeignKey(Shift,    on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    # computed fields:
    @computed(models.SlugField(max_length=20), depends=[('self',['workday','shift'])])
    def slug (self):
        return self.workday.slug + '-' + self.shift.name

    @computed(models.DateTimeField(), depends=[('self',['workday','shift'])])
    def start (self):
        return dt.datetime.combine(self.workday.date, self.shift.start)

    @computed(models.DateTimeField(), depends=[('self',['workday','shift'])])
    def end (self):
        return dt.datetime.combine(self.workday.date, self.shift.start) + self.shift.duration

    def __str__(self) :
        return str(self.workday) + ' ' + str(self.shift)

    def get_absolute_url(self):
        return reverse("slot", kwargs={"slug": self.slug})

    objects = SlotManager.as_manager()

# ============================================================================
class ShiftTemplate (models.Model) :
    # fields: name, start, duration 
    shift       = models.ForeignKey(Shift, on_delete=models.CASCADE)
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    ppd_id      = models.IntegerField()

    def weekAB (self):
        if self.ppd_id < 7:
            return 'A'
        else:
            return 'B'
    
    def weekday (self, text=False):
        days = "Sun Mon Tue Wed Thu Fri Sat".split()
        if text:
            return days[self.ppd_id % 7]
        return self.ppd_id % 7

    def __str__(self) :
        return f'{self.shift.name} Template'

    def get_absolute_url(self):
        return reverse("shifttemplate", kwargs={"pk": self.pk})
    
    @property
    def nickname (self):
        return f'{self.weekday(text=True)}-{self.weekAB()}'

    class Meta:
        unique_together = ['shift', 'ppd_id']

# ============================================================================
class PtoRequest (models.Model): 
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    workday   = models.ForeignKey(Workday, on_delete=models.CASCADE)
    manager_approval = models.BooleanField(default=False)
    stands_respected = models.BooleanField(default=False)

    def __str__(self) :
        # ex: "<JOSH PTOReq: Sep5>"
        return f'<{self.employee} PTOReq: {self.workday.date.strfmt("%m%d")}>'
