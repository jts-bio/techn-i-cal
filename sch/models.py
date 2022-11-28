import datetime as dt
from re import sub

from computedfields.models import ComputedFieldsModel, computed
from django.db import models
from django.db.models import (Avg, Count, DurationField, ExpressionWrapper, F,
                              FloatField, Max, Min, OuterRef, Q, QuerySet,
                              StdDev, Subquery, Sum, Variance)
from django.urls import reverse
from multiselectfield import MultiSelectField
from collections import Counter
"""
DJANGO PROJECT:     TECHNICAL
APPLICATION:        FLOW-RATE SCHEDULING (SCH)

AUTHOR:             JOSH STEINBECKER        
========================================================

Models: 
    - Shift
    - Employee
    - EmployeeClass
    - Workday
    - Slot
    - PtoRequest
    - ShiftPreference
"""

DAYCHOICES              = (
                (0, 'Sunday'),
                (1, 'Monday'),
                (2, 'Tuesday'),
                (3, 'Wednesday'),
                (4, 'Thursday'),
                (5, 'Friday'),
                (6, 'Saturday')
            )
WEEKABCHOICES           = (
                (0, 'A'),
                (1, 'B'),)
TODAY                   = dt.date.today ()
TEMPLATESCH_STARTDATE   = dt.date (2020,1,12)
SCH_STARTDATE_SET       = [(TEMPLATESCH_STARTDATE + dt.timedelta(days=42*i)) for i in range (200)]
PRIORITIES              = (
                ('L', 'Low'),
                ('M', 'Medium'),
                ('H', 'High'),
                ('U', 'Urgent'),
            )
PREF_SCORES             = (
                    ('SP', 'Strongly Prefer'),
                    ('P', 'Prefer'),
                    ('N', 'Neutral'),
                    ('D', 'Dislike'),
                    ('SD', 'Strongly Dislike'),
                )
PTO_STATUS_CHOICES      = (
                    ('P', 'Pending'),
                    ('A', 'Approved'),
                    ('D', 'Denied'),
                )


def YEAR_SCHDATES (year):
    all_ = [TEMPLATESCH_STARTDATE + dt.timedelta(days=i*42) for i in range(-100,100)]
    inYear = []
    for d in all_:
        if d.year == year:
            inYear.append(d)
    return inYear
#* --- ---    Managers    --- --- *#
# ============================================================================
class ShiftManager (models.QuerySet):

    def on_weekday (self, weekday) -> QuerySet:
        return self.filter(occur_days__contains=weekday)

    def on_workday (self, workday):
        return self.filter(occur_days__contains=workday.iweekday)

    def to_fill (self,workday):
        slot_exits = Slot.objects.filter(workday=workday).values('shift')
        return self.all().exclude(pk__in=slot_exits)

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
    def empls_weekly_hours (self, year, week, employee):
        return self.filter(
            workday__iweek= week,
            workday__date__year= year,
            employee= employee
            ).aggregate(hours=Sum('shift__hours'))

    def turnarounds (self):
        turnarounds = []
        for i in self.all():
            if i.is_turnaround:
                turnarounds.append(i.pk)
        return self.filter(pk__in=turnarounds)
    
    def preturnarounds (self):
        preturnarounds = []
        for i in self.all():
            if i.is_preturnaround:
                preturnarounds.append(i.pk)
        return self.filter(pk__in=preturnarounds)

    def incompatible_slots (self, workday, shift):
        if shift.start <= dt.time(10,0,0):
            dayBefore = workday.prevWD()
            incompat_shifts = dayBefore.shifts.filter(start__gte=dt.time(10,0,0))
            incompat_slots = self.filter(workday=dayBefore,shift__in=incompat_shifts)
            return incompat_slots
        elif shift.start >= dt.time(20,0,0):
            dayAfter = workday.nextWD()
            incompat_shifts = dayAfter.shifts.filter(start__lt=dt.time(20,0,0))
            incompat_slots = self.filter(workday=dayAfter,shift__in=incompat_shifts)
            return incompat_slots
        elif shift.start >= dt.time(10,0,0):
            dayAfter = workday.nextWD()
            incompat_shifts = dayAfter.shifts.filter(start__lt=dt.time(10,0,0))
            incompat_slots = self.filter(workday=dayAfter,shift__in=incompat_shifts)
            return incompat_slots
        
    def belowAvg_sftPrefScore (self):
        query = self.annotate(
            score = ShiftPreference.objects.filter(employee=OuterRef('employee'), shift=OuterRef('shift')).values('score'))
        
        # return Slots whose shift pref score for their associated employee is below that employees average shift pref score.
        # 1 -- Get employee avg pref score
        emplAvgs = Employee.objects.avg_shift_pref_score()
        
        # 2 -- Subquery on Slots 
        query = query.annotate(
            avgScore = Subquery(Employee.objects.avg_shift_pref_score().filter(pk=OuterRef('employee__pk')).values('avgSftPref')))
        
        # 3 -- For all slots, ExprWrap their shift pref score - avg score: below avg shift pref score will be negative after this
        score = ExpressionWrapper((F('score') - F('avgScore')) , output_field=FloatField())
        query = query.annotate(
            change = score
            )
        
        # 4 -- return only slots whose shift pref score is less than 0
        return query.filter(change__lte=0)
    
    def streaks (self, employee):
        return self.filter(employee=employee, is_terminal=True)
    
    def sch__pmSlots (self, year, sch):
        return self.objects.filter(workday__date__year=year,workday__ischedule=sch, shift__start__hour__gte=12)
    
    def tally_schedule_streaks (self, employee, year, schedule):
        return tally(list(self.filter(employee=employee, is_terminal=True, workday__date__year=year, workday__ischedule=schedule).values_list('streak')))        
class TurnaroundManager (models.QuerySet):
    def schedule (self, year, number):
        sch = Schedule.objects.get(year=year,number=number)
        return Slot.objects.filter(workday__schedule=sch)
         
# ============================================================================
class EmployeeManager (models.QuerySet):
    def low_option_emps (self):
        return self.filter (fte__gt=0, n_trained__lte=3)
    def trained_for (self,shift):
        """
        VERIFIED WORKING
        """
        return self.filter(shifts_trained=shift)
    def in_slot (self, shift, workday):
        return self.filter(slot__shift__name=shift, slot__workday=workday)
    def in_other_slot (self, shift, workday):
        e = Slot.objects.filter(workday=workday).exclude(shift=shift).values('employee')
        return self.filter(pk__in=e)
    def weekly_hours (self, year, week):
        return Employee.objects.annotate(
                hours=Subquery(Slot.objects.filter(workday__date__year=year,workday__iweek=week, employee=F('pk')).aggregate(hours=Sum('hours')))
            )
    def can_fill_shift_on_day (self, shift, workday, method="available"):
        shift = Shift.objects.get(name=shift)
        shift_len = shift.hours
        
        if method == "available":
            employees = Employee.objects.filter(shifts_available=shift)
        elif method == "trained":
            employees = Employee.objects.filter(shifts_trained=shift)
           
        # Exclusion 1-- Empl 
        in_other    = Employee.objects.in_other_slot(shift, workday) # empls in other slots (should be exculded)
        has_pto_req = PtoRequest.objects.filter(workday=workday.date, status__in=['A','P']).values('employee')
        employees   = employees.exclude(pk__in=in_other).exclude(pk__in=has_pto_req)
        weeklyHours = {empl: Slot.objects.empls_weekly_hours(workday.date.year,workday.iweek,empl) for empl in employees}
        
        for empl in weeklyHours:
            if weeklyHours[empl]['hours'] is None:
                weeklyHours[empl]['hours'] = 0
                weeklyHours[empl]['weeklyPercent'] = 0
            if empl.fte == 0:
                weeklyHours[empl]['weeklyPercent'] = 1
            else:
                weeklyHours[empl]['weeklyPercent'] = weeklyHours[empl]['hours']/( empl.fte  * 40)
        # find min value for weeklyPercent
        if weeklyHours:
            minPercent = min(weeklyHours.values(), key=lambda x: x['weeklyPercent'])
        else:
            minPercent = 0
        return Employee.objects.filter(pk__in=[empl.pk for empl in weeklyHours if weeklyHours[empl]['hours'] + shift_len <= 40]) 
    def can_fill_shift_on_day_ot_overide (self, shift, workday, method="available"):
        week = workday.iweek
        year = workday.date.year
        shift_len = (shift.duration - dt.timedelta(minutes=30)).total_seconds() / 3600

        if method == "available":
            employees = Employee.objects.filter(shifts_available=shift)
        elif method == "trained":
            employees = Employee.objects.filter(shifts_trained=shift)
        in_other = Employee.objects.in_other_slot(shift, workday) # empls in other slots (should be exculded)
        has_pto_req = PtoRequest.objects.filter(workday=workday.date, status__in=['A','P']).values('employee')
        employees = employees.exclude(pk__in=in_other).exclude(pk__in=has_pto_req)
        return employees.filter(shifts_trained=shift).exclude(pk__in=in_other).exclude(pk__in=has_pto_req)
    def who_worked_evening_day_before (self, workday):
        dateBefore = workday.date - dt.timedelta(days=1)
        slots = Slot.objects.filter(workday__date=dateBefore, shift__start__gte=dt.time(12,0,0))
        return slots.values('employee')
    def weekly_hours (self, year, week):
        return self.filter(slot__workday__iweek=week, slot__workday__date__year=year).aggregate(hours=Sum('slot__hours'))
    def avg_shift_pref_score (self):
        return self.annotate(
            avgSftPref=Avg(Subquery(ShiftPreference.objects.filter(
                employee=OuterRef('pk')).values('score'),output_field=FloatField())))
    def workEveningBefore (self,workday):
        emps = Slot.objects.filter(workday__date=workday.prevWD(),shift__start__hour__gte=12).values('employee')
        return self.filter(pk__in=emps)
    def workMorningAfter (self,workday):
        emps = Slot.objects.filter(workday__date=workday.nextWD(),shift__start__hour__lte=9).values('employee')
        return self.filter(pk__in=emps)
    def availableFor (self,shift):
        emps = self.filter(shifts_available=shift)
        return emps
    def inConflictingSlot (self,slot):
        if slot.shift.start.hour > 10:
            return Employee.workMorningAfter(slot.workday)
        if slot.shift.start.hour < 10:
            return self.workEveningBefore(slot.workday)
# ============================================================================
class ShiftPreferenceManager (models.QuerySet):
    
    def below_average(self, employee):
        average = employee.avg_shift_pref_score 
        return self.filter(employee=employee, score__lt=average)
# ============================================================================  
class WorkdayManager (models.QuerySet):
    def in_week(self, year, iweek):
        return self.filter(date__year=year, iweek=iweek)

    def same_week (self, workday):
        week = workday.iweek
        year = workday.date.year
        return self.filter(iweek=week, date__year=year)
# ============================================================================  
class EmployeeClass (models.Model):
    id          = models.CharField(max_length=5, primary_key=True)
    class_name  = models.CharField(max_length=40)
# ============================================================================
#************************************#
#* --- ---      MODELS      --- --- *#
#************************************#
# ============================================================================
class Shift (ComputedFieldsModel) :
    """
    model <<< SHIFT >>>
    
        hours               ---> 10.0
        on_days_display     ---> "Sun Mon Tue Wed Thu Fri Sat"
        ppd_ids             ---> 0,1,2,3,4,5,6,7,8,9,10,11,12,13
        
    
    """
    # fields: name, start, duration 
    name            = models.CharField (max_length=100)
    cls             = models.CharField (max_length=5, choices=(('CPhT','CPhT'),('RPh','RPh')), null=True)
    start           = models.TimeField()
    duration        = models.DurationField()
    group           = models.CharField(max_length=10, choices=(('AM','AM'),('MD','MD'),('PM','PM'),('XN','XN')), null=True)
    occur_days      = MultiSelectField (choices=DAYCHOICES, max_choices=7, max_length=14, default=[0,1,2,3,4,5,6])
    is_iv           = models.BooleanField (default=False)

    def __str__(self) :
        return self.name

    def url(self):
        return reverse("shift", kwargs={"name": self.name})

    @computed(models.FloatField(), depends=[('self', ['duration'])])
    def hours (self):
        return self.duration.total_seconds() / 3600 - 0.5

    @property
    def on_days_display (self):
        return " ".join(["Sun Mon Tue Wed Thu Fri Sat".split(" ")[int(i)] for i in self.occur_days])

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
    def sd_ids(self):
        """
        """
        ids = list(self.occur_days)
        for i in self.occur_days:
            for x in [7,14,21,28,35]:
                ids.append(str(int(i)+x))
        return sorted(ids)
        

    @property
    def end (self):
        return (dt.datetime(2022,1,1,self.start.hour,self.start.minute) + self.duration).time()

    @property
    def info_prefRatio (self):
        likes = ShiftPreference.objects.filter(score__gt=0,shift=self).count()
        dislikes = ShiftPreference.objects.filter(score__lt=0,shift=self).count()
        if dislikes != 0:
            return round (likes/dislikes,  2)
        else:
            return 0

   

    objects = ShiftManager.as_manager()
# ============================================================================
class Employee (ComputedFieldsModel) :
    # fields: name, fte_14_day , shifts_trained, shifts_available 
    name            = models.CharField (max_length=100)
    fte_14_day      = models.FloatField()
    shifts_trained  = models.ManyToManyField (Shift, related_name='trained')
    shifts_available= models.ManyToManyField (Shift, related_name='available')
    streak_pref     = models.IntegerField (default=3)
    trade_one_offs  = models.BooleanField (default=True)
    cls             = models.CharField (choices=(('CPhT','CPhT'),('RPh','RPh')),default='CPhT',blank=True, null=True,max_length=4)
    evening_pref    = models.BooleanField (default=False)
    slug            = models.SlugField (blank=True,null=True)
    hire_date       = models.DateField (default=dt.date(2018,4,11))
    n_trained       = models.IntegerField (default=1)

    @property
    def yrs_experience (self):
        return round((TODAY - self.hire_date).days / 365, 2)
    
    def __str__(self) :
        return self.name
    # computed fields:

    @computed(models.FloatField(), depends=[('self',['fte_14_day'])])
    def fte (self):
        return self.fte_14_day / 80

    def url(self):
        return reverse("employee-detail", kwargs={"name": self.name})

    def weekly_hours (self, year, iweek):
        return Slot.objects.filter(workday__date__year=year,workday__iweek=iweek, employee=self).aggregate(hours=Sum('hours'))['hours']

    def weekly_hours_perc (self,year, iweek):
        """
        Returns the ratio of hours worked to hours scheduled.
        """
        if self.fte == 0:
            return 1
        if self.weekly_hours(year,iweek) == None:
            return 0
        return round(self.weekly_hours(year,iweek)/(self.fte*80/2),2)

    def period_hours (self, year, iperiod):
        return Slot.objects.filter(workday__date__year=year,workday__iperiod=iperiod, employee=self).aggregate(hours=Sum('hours'))['hours']

    @property
    def avg_shift_pref_score (self):
        return Employee.objects.filter(pk=self.pk).annotate(
            avgSftPref=Avg(Subquery(ShiftPreference.objects.filter(
                employee=OuterRef('pk')).values_list('score',flat=True),output_field=FloatField())))[0].avgSftPref
    
    @property
    def agg_avg_shift_pref_score (self):
        return ShiftPreference.objects.filter(employee=self).values('score').aggregate(Avg('score'))['score__avg']
    
    @property
    def templated_days (self): 
        return ShiftTemplate.objects.filter(employee=self)
    
    @property
    def templated_days_display (self):
        return " ".join([s.day for s in self.templated_days])
    
    @property
    def templated_days_off (self):
        return TemplatedDayOff.objects.filter(employee=self)
    
    @property
    def templated_days_off_display (self):
        tdoAll = list(TemplatedDayOff.objects.all().order_by('sd_id').values_list('sd_id',flat=True).distinct())
        empTdos = TemplatedDayOff.objects.filter(employee=self)
        string = ""
        for v in tdoAll:
            if empTdos.filter(sd_id=v):
                string += "X"
            else:
                string += "."
        segs = []
        while len(string) > 7:
            segs += [string[:7]]
            string = string[7:]
        segs += [string]
        return segs
    
    def tdo_idList (self):
        """A list of SD_ID values for the employees TDOs"""
        return list(self.templated_days_off.values_list('sd_id',flat=True))
    
    def tdo_weekend_idList (self):
        """A subset of employees tdo_idList filtered to only include days that are weekends"""
        weekend = []
        allList = self.tdo_idList()
        for i in allList:
            if i % 7 == 0 or i % 7 == 6:
                weekend += [i]
        return weekend
    
    def getCoworkersOnSameWeekend (self):
        """
        Returns Employee objects which match their TDO pattern on Weekend Days
        """
        weekend_group = []
        for emp in Employee.objects.all():
            if emp.tdo_weekend_idList() == self.tdo_weekend_idList():
                weekend_group += [emp.pk]
        return Employee.objects.filter(pk__in=weekend_group)
    
    def ftePercForWeek (self, year, iweek):
        if self.fte == 0:
            return 0.8
        if self.weekly_hours(year,iweek) == None:
            return 0
        return  self.weekly_hours(year,iweek) / (Employee.objects.get(pk=self.pk).fte_14_day/ 2)
    
    def count_shift_occurances (self):
        slots = Slot.objects.filter(employee=self).values('shift__name')
        return slots.distinct().annotate(count=Count('shift__name'))
    
    def unfavorable_shifts (self):
        if self.evening_pref:
            return self.shifts_available.filter(start__hour__lte=10)
        if not self.evening_pref:
            return self.shifts_available.filter(start__hour__gt= 10)
    
    @property
    def get_TdoSlotConflicts (self):
        tdos = list(TemplatedDayOff.objects.filter(employee=self).values_list('pk',flat=True))
        return Slot.objects.filter(workday__sd_id__in=tdos, employee=self)

    def info_printWeek(self,year,week):
            slots = list(Slot.objects.filter(employee=self,workday__date__year=year,workday__iweek=week).values_list('shift__name',flat=True))
            return f'{self.name}: {slots}'
        
    def save (self, *args, **kwargs):
        slugString = self.name.strip().replace(" ","-")
        self.slug      = slugString
        self.n_trained = self.shifts_trained.count()
        super(*args,**kwargs).save()
        
    
       
    objects = EmployeeManager.as_manager()
# ============================================================================
class Workday (ComputedFieldsModel) :
    # fields: date, shifts 
    date = models.DateField()
    week = models.ForeignKey("week", on_delete=models.CASCADE, null=True, related_name='workdays')
    period = models.ForeignKey("Period", on_delete=models.CASCADE, null=True,related_name='workdays')
    schedule = models.ForeignKey("Schedule", on_delete=models.CASCADE,null=True,related_name='workdays')

    __all__ = ['date','slug','iweekday','iweek','iperiod','ppd_id','weekday',
               'shifts',
               'filledSlots','n_slots',"n_emptySlots",'n_shifts','percFilled',
               'siblings_iweek']
    
    @property
    def version (self):
        return self.schedule.version

    @computed(models.SlugField(max_length=20), depends=[('self',['date'])])
    def slug (self) : 
        return self.date.strftime('%Y-%m-%d')
    @computed(models.IntegerField(null=True), depends=[('self',['date'])])
    def iweekday (self) :
        # range 0 -> 6
        return int (self.date.strftime('%w'))
    @computed(models.IntegerField(null=True), depends=[('self',['date'])])
    def iweek (self) :
        # range 0 -> 53
        return int (self.date.strftime('%U'))
    @property 
    def pto (self):
        return PtoRequest.objects.filter(workday=self.date)
    @computed(models.IntegerField(), depends=[('self',['date'])])
    def iperiod (self) :
        # range 0 -> 27
        return int (self.date.strftime('%U')) // 2

    @computed(models.IntegerField(), depends=[('self',['date'])])
    def ppd_id (self) :
        # range 0 -> 13
        return (self.date - TEMPLATESCH_STARTDATE).days % 14
    
    @computed(models.CharField(max_length=20,null=True), depends=[('self',['iperiod'])])
    def ischedule (self) :
        # range 0 -> 9
        if self.iperiod:
            return self.iperiod // 3 
        else:
            return 

    @computed(models.IntegerField(),depends=[('self',['date'])])
    def sd_id (self) :
        # range 0 -> 41
        return (self.date - TEMPLATESCH_STARTDATE).days % 42
    
    @property
    def weekday (self): 
        # Sun -> Sat
        return self.date.strftime('%a')
    
    @property
    def shifts (self) :
        return Shift.objects.filter(occur_days__contains= self.iweekday) 
    
    @property
    def filledSlots (self) :
        return self.slots.exclude(employee=None)
    
    @property
    def n_slots (self) :
        return Slot.objects.filter(workday=self).count()
    
    @property
    def emptySlots (self) :
        return self.slots.filter(employee=None)

    @property
    def n_shifts (self) :
        return Shift.objects.filter(occur_days__contains= self.iweekday).count()
    
    @property
    def n_empty (self) :
        return self.n_unfilled
    
    @property
    def percFilled (self) -> float:
        slots = Slot.objects.filter(workday=self)
        return slots.count() / self.n_shifts

    @property
    def siblings_iweek (self) -> "WorkdayManager":
        return Workday.objects.same_week(self) # type: ignore

    @property
    def iweek_of (self) :
        return self.siblings_iweek.first()

    @property
    def siblings_iperiod (self):
        return Workday.objects.filter(date__year=self.date.year, iperiod=self.iperiod)

    @property
    def iperiod_of (self) :
        return self.siblings_iperiod.first()

    def __str__ (self) :
        return str(self.date.strftime('%Y %m %d'))

    def url (self) :
        return reverse("workday", kwargs={"sch": self.schedule.pk,"slug": self.slug})
    
    def prevWD (self) :
        try:
            return Workday.objects.get(date=self.date - dt.timedelta(days=1))
        except Workday.DoesNotExist:
            return self

    def nextWD (self) :
        try:
            return Workday.objects.get(date=self.date + dt.timedelta(days=1))
        except Workday.DoesNotExist:
            return self
    
    def prevURL (self) :
        try:
            return reverse("workday", kwargs={
                               "slug": (self.date - dt.timedelta(days=1)).strftime('%Y-%m-%d'), 
                               "schid": self.schedule.pk })
        except Workday.DoesNotExist:
            return self.url()

    def nextURL (self) :
        try:
            return reverse("workday", kwargs={
                                "slug": (self.date + dt.timedelta(days=1)).strftime('%Y-%m-%d'),
                                "schid": self.schedule.pk})
        except Workday.DoesNotExist:
            return self.url()

    @property
    def days_away (self) :
        td = self.date - TODAY 
        return td.days

    def related_slots (self) :
        return Slot.objects.filter(workday=self)

    @property
    def n_unfilled (self) :
        return  self.n_shifts - self.related_slots().count()
    
    @property
    def list_unpref_slots (self):
        return self.filledSlots.annotate(
                score=Subquery(ShiftPreference.objects.filter(employee=OuterRef('employee'),shift=OuterRef('shift')).values('score'))
            ).filter(score__lt=0)
        
    @property
    def areTemplateSlotsFilled (self):
        tslots = ShiftTemplate.objects.filter(ppd_id=self.ppd_id).values_list('shift',flat=True)
        for shift in tslots:
            if not self.filledSlots.filter(shift=shift).exists():
                return False
        return True
    
    @property
    def printSchedule (self):
        slots = Slot.objects.filter(workday=self)
        for slot in slots :
            print(slot.shift.name, slot.employee)
        
    def who_can_fill (self, shift):
        if shift not in self.shifts:
            return None
        if Slot.objects.filter(workday=self,shift=shift).exists():
            current = Slot.objects.get(workday=self,shift=shift).employee
            return Employee.objects.can_fill_shift_on_day(
                workday=self,shift=shift) | Employee.objects.filter(
                    pk=current.pk)
        return Employee.objects.can_fill_shift_on_day(workday=self,shift=shift)
    
    def n_can_fill (self, shift):
        if self.who_can_fill == None:
            return None 
        return len (self.who_can_fill(shift))
    
    def template_exceptions (self):
        templates = ShiftTemplate.objects.filter(ppd_id=self.sd_id)
        ptoReqs   = PtoRequest.objects.filter(workday=self.date)
        excepts = []
        for templ in templates:
            if ptoReqs.filter(employee=templ.employee).exists():
                excepts.append(templ)
        return excepts
    
    def save      (self, *args, **kwargs) :
        super().save(*args,**kwargs)
        self.post_save()
    def post_save (self):
        for i in self.shifts:
            if not Slot.objects.filter(workday=self,shift=i).exists():
                s = Slot.objects.create(workday=self,shift=i,week=self.week,period=self.period,schedule=self.schedule)
                s.save()
    def url (self):
        return self.week.url() + f'{self.slug}/'
    
    objects = WorkdayManager.as_manager()
# ============================================================================  
class Week (ComputedFieldsModel) :
    __all__ = [
        'year','iweek','prevWeek','nextWeek',
    ]
    
    iweek       = models.IntegerField (null=True, blank=True) 
    year        = models.IntegerField (null=True, blank=True)
    number      = models.IntegerField (null=True, blank=True)
    period      = models.ForeignKey   ("Period", on_delete=models.CASCADE, null=True,related_name='weeks')
    schedule    = models.ForeignKey   ("Schedule", on_delete=models.CASCADE, null=True,related_name='weeks')
    start_date  = models.DateField    (blank=True, null=True)
    
    @property
    def version (self):
        return self.schedule.version
    
    def unfavorables (self):
        return self.slots.filter(empl_sentiment__lt=50)
    def empl_needed_hrs (self,empl):
        slots = self.slots.filter(employee=empl)
        wds = slots.values('workday__date')
        hrs   = slots.aggregate(Sum('shift__hours'))['shift__hours__sum']
        if hrs is None:
            hrs = 0
        needed = empl.fte_14_day / 2
        pto = PtoRequest.objects.filter(employee=empl,workday__in=wds)
        pto_hrs = pto.count() * 10
        needed = needed - (hrs + pto_hrs)
        if needed < 0:
            needed = 0
        return needed
    def needed_hours (self):
        """
        >>> {<Josh> : 10, <Sabrina> : 5 }
        """
        empls = Employee.objects.filter(fte__gt=0)
        output = {}
        for empl in empls:
            hrs_needed = self.empl_needed_hrs(empl)
            output.update({empl:hrs_needed})
        return sortDict(output)
    def empl_with_max_needed_hours (self):   
        return self.needed_hours()[0]
    @property
    def dates (self):
        return [self.start_date + dt.timedelta(days=i) for i in range(7)]
    @property
    def workdays (self):
        dates  = self.dates
        return Workday.objects.filter (date__in=dates)   
    @property
    def slug (self) : 
        return f'{self.year}_{self.number}'
    @property
    def name     (self) : 
        return f'{self.year}_{self.iweek}'   
    def prevWeek (self) :
        try:
            return Week.objects.get(year=self.year, iweek=self.iweek-1)
        except Week.DoesNotExist:
            # go back 1 year, and get the max iweek of that year.
            yearnew = self.year - 1
            iweeknew = Week.objects.filter(year=yearnew).aggregate(Max('iweek'))['iweek__max']
            return Week.objects.get(year=yearnew, iweek=iweeknew)   
    def nextWeek (self) :
        try:
            return Week.objects.get(year=self.year, iweek=self.iweek+1)
        except Week.DoesNotExist:
            # go forward 1 year, and get the 0 iweek of that year.
            yearnew = self.year + 1
            try:
                return Week.objects.get(year=yearnew, iweek=0)
            except:
                return Week.objects.get(year=yearnew, iweek=1)
    @property
    def slots    (self) :
        dates = self.dates
        return Slot.objects.filter(workday__date__in=dates)
    def n_options_for_slots (self):
        possibles = []
        for s in self.slots.all():
            possibles += s.fillableBy()
        return sortDict (tally (possibles))          
    def __str__   (self) :
        return f'WEEK-{self.year}.{self.number}'
    def save      (self, *args, **kwargs) :
        super().save(*args,**kwargs)
        self.post_save()
    def post_save (self):
        for i in self.dates:
            if not Workday.objects.filter(date=i,week=self).exists():
                d = Workday.objects.create(date=i,week=self,period=self.period,schedule=self.schedule)
                d.save()
    def url (self) : 
        return self.period.url() + f"W{self.number}/"
# ============================================================================  
class Period (models.Model):
    year       = models.IntegerField()
    number     = models.IntegerField()
    start_date = models.DateField()
    schedule   = models.ForeignKey('Schedule', on_delete=models.CASCADE,related_name='periods')
    
    @property
    def week_start_dates (self):
        return [self.start_date + dt.timedelta(days=i*7) for i in range(2)]
    
    def save (self, *args, **kwargs) :
        super().save(*args,**kwargs)
        self.post_save()
    def post_save (self):
        for i in self.week_start_dates:
            if not Week.objects.filter(start_date=i,period=self).exists():
                w = Week.objects.create(start_date=i,year=i.year,number=i.strftime("%U"),period=self,schedule=self.schedule)
                w.save()  
    def url (self):
        return self.schedule.url() + f"P{self.number}/"
    def __str__(self):
        return f'PayPeriod {self.year}.{self.number}.{self.schedule.version}'

class Schedule (models.Model):
    year       = models.IntegerField(null=True,default=None)
    number     = models.IntegerField(null=True,default=None)
    start_date = models.DateField()
    status     = models.IntegerField(choices=list(enumerate("working,finished,discarded")),default=0)
    version    = models.CharField(max_length=1,default='A')
    

    @property
    def week_start_dates (self):
        return [self.start_date + dt.timedelta(days=i*7) for i in range(6)]
    @property
    def payPeriod_start_dates (self):
        return [self.start_date + dt.timedelta(days=i*14) for i in range(3)]
    
    def save (self, *args, **kwargs) :
        if self.year == None :
            self.year = self.start_date.year
        if self.number == None :
            self.number = int (self.start_date.strftime("%U")) // 6
        super().save(*args, **kwargs)
        self.post_save()
    def post_save (self) :
        
        for pp in self.payPeriod_start_dates:
            if not Period.objects.filter(start_date=pp,schedule=self).exists():
                p = Period.objects.create(start_date=pp,year=pp.year,number=int(pp.strftime("%U"))//2,schedule=self)
                p.save()
        
        sameYrNum = Schedule.objects.filter(year=self.year,number=self.number)
        if sameYrNum.exists():
            n = sameYrNum.count()
            if n:
                self.version = "ABCDEFGHIJ"[n]
                
    def url (self) :
        url = f"/sch/v2/S{self.year}-{self.number}{self.version}/"
        return url

    def __str__ (self):
        return f"S{self.year}-{self.number}{self.version}"
# ============================================================================
class Slot (ComputedFieldsModel) :
    # fields: workday, shift, employee
    workday        = models.ForeignKey ("Workday",  on_delete=models.CASCADE, related_name='slots')
    shift          = models.ForeignKey ( Shift,     on_delete=models.CASCADE, related_name='slots')
    employee       = models.ForeignKey ("Employee", on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='slots')
    empl_sentiment = models.SmallIntegerField (null=True,default=None)   
    conflicting_slots = models.ManyToManyField("Slot", null=True,default=None)
    fillableByN    = models.SmallIntegerField(default=0)
    
    week           = models.ForeignKey (Week, on_delete=models.CASCADE, null=True, related_name='slots')
    period         = models.ForeignKey (Period, on_delete=models.CASCADE, null=True, related_name='slots')
    schedule       = models.ForeignKey (Schedule, on_delete=models.CASCADE, null=True,related_name='slots')
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workday", "shift"], name='Shift Duplicates on day'),
            models.UniqueConstraint(fields=["workday", "employee"], name='Employee Duplicates on day')
        ]
        
    # computed fields:
    @computed(models.SlugField(max_length=20), depends=[('self',['workday','shift'])])
    def slug    (self):
        return self.workday.slug + '-' + self.shift.name
    def start   (self):
        return dt.datetime.combine(self.workday.date, self.shift.start)
    def end     (self):
        return dt.datetime.combine(self.workday.date, self.shift.start) + self.shift.duration
    @computed(models.FloatField(), depends=[('self',['shift'])])
    def hours   (self) :
        return (self.shift.duration.total_seconds() - 1800) / 3600 
    def __str__ (self) :
        return str(self.workday.date.strftime('%y%m%d')) + '-' + str(self.shift) + " " + str(self.employee)
    def get_absolute_url (self):
        return reverse("slot", kwargs={"slug": self.slug})
    @property
    def prefScore        (self) :
        if ShiftPreference.objects.filter(shift=self.shift, employee=self.employee).exists() :
            return ShiftPreference.objects.get(shift=self.shift, employee=self.employee).score
        else:
            return 0
    @computed (models.IntegerField(), depends=[('self',['workday'])])
    def is_turnaround    (self) :
        if not self.employee:
            return False
        if self.shift.start > dt.time(12,0):
            return False
        elif self.shift.start > dt.time(10):
            if Slot.objects.filter(workday=self.workday.prevWD(), shift__start__gt=dt.time(12,0), employee=self.employee).count() > 0 :
                return True 
        elif self.shift.start < dt.time(12,0) :
            if Slot.objects.filter(workday=self.workday.prevWD(), shift__start__gt=dt.time(10,0), employee=self.employee).count() > 0 :
                return True
            else:
                return False
    @computed (models.IntegerField(), depends=[('self',['workday'])])
    def is_preturnaround (self) :
        if not self.employee:
            return False
        if self.shift.start < dt.time(12,0):
            return False
        elif self.shift.start > dt.time(12,0) :
            if Slot.objects.filter(workday=self.workday.nextWD(), shift__start__lt=dt.time(12,0), employee=self.employee).count() > 0 :
                return True
            else:
                return False
    def turnaround_pair  (self) :
        self.save()
        if self.is_turnaround :
            return Slot.objects.get(employee=self.employee,workday=self.workday.prevWD())
        if self.is_preturnaround :
            return Slot.objects.get(employee=self.employee,workday=self.workday.nextWD())
        else:
            return None
    @computed (models.BooleanField(), depends=[('self',['workday'])])
    def is_terminal      (self) :
        if Slot.objects.filter(workday=self.workday.nextWD(), employee=self.employee).exists() :
            return False
        else:
            return True
    @property   
    def siblings_day     (self) :
        return Slot.objects.filter(workday=self.workday).exclude(shift=self.shift)  
    @property
    def tenable_trades (self):
        primaryScore   = self.prefScore
        primaryShift   = self.shift
        otherShifts    = self.siblings_day.values('shift')
        otherEmployees = self.siblings_day.values('employee')
        return ShiftPreference.objects.filter(employee=self.employee,shift=self.shift,score__gt=primaryScore)   
    @computed (models.IntegerField(), depends=[('self', ['workday','shift'])])          
    def streak (self):
        # count the streak of slots in a row this employee has had
        i = 1
        while Slot.objects.filter(workday__date=self.workday.date - dt.timedelta(days=i),employee=self.employee).exists():
            i = i + 1
        return i
    @computed (models.BooleanField(), depends=[('self', ['employee'])])
    def isOverStreakPref (self):
        if not self.employee:
            return False
        if self.streak:
            return self.streak > self.employee.streak_pref
        else:
            return False
    @property 
    def shouldBeTdo (self):
        """EMPLOYEE SHOULD NOT WORK THIS DAY BECAUSE OF A TEMPLATED DAY OFF OBJECT"""
        if TemplatedDayOff.objects.filter(employee=self.employee, sd_id=self.workday.sd_id).exists():
            return True
        else:
            return False
    def _fillableBy (self):
        """ 
        returns Employees that could fill this slot 
        
        BASED ON
        ------------------------------------------------
            - training, 
            - not in conflicting slots 
                - on day before, 
                - day of, or 
                - day after     
                
        EXAMPLE
        ------------------------------------------------
        ```s.fillableBy() 
        >>>   [<Employee: Josh, Brianna, Sabrina...>]
        ```
        """
        trained = Employee.objects.filter(shifts_trained=self.shift)
        
        in_conflicting= self.conflicting_slots.all().values('employee__name').distinct()
        sd= self.workday.sd_id
        has_tdo= TemplatedDayOff.objects.filter (sd_id=sd).values('employee')
        has_ptor= PtoRequest.objects.filter (workday=self.workday.date).values('employee')
        
        conflicting_empls = list(in_conflicting.union(has_tdo).union(has_ptor).values_list('pk',flat=True))
        if None in conflicting_empls:
            idx = conflicting_empls.index(None)
            conflicting_empls.pop(idx)
        can_fill = trained.exclude(pk__in=conflicting_empls)
        
        return can_fill         
    def isFromTemplate (self):
        if self.employee:
            if ShiftTemplate.objects.filter(ppd_id=self.workday.sd_id, employee=self.employee).exists():
                return True
            else:
                return False  
    def _get_conflicting_slots (self):
        sch = self.schedule
        if self.shift.start.hour > 10:
            slots = Slot.objects.filter(schedule=sch, workday=self.workday.nextWD(), shift__start__hour__lt=10)
        elif self.shift.start.hour < 10:
            slots = Slot.objects.filter(schedule=sch, workday=self.workday.prevWD(), shift__start__hour__gt=10)
        elif self.shift.start.hour == 10:
            slots = Slot.objects.filter(schedule=sch, workday=self.workday.nextWD(), shift__start__hour__lt=10) | Slot.objects.filter(workday=self.workday.prevWD(), shift__start__hour__gt=10)
        sameDaySlots = Slot.objects.filter(schedule=sch, workday=self.workday).exclude(pk=self.pk)
        slots = slots.union(sameDaySlots)
        return slots
    def set_sst (self):
        if PtoRequest.objects.filter(workday=self.workday.date, employee=self.employee).exists():
            return "NA"
        sst = ShiftTemplate.objects.filter(ppd_id=self.workday.sd_id)
        if sst.exists():
            wk_needed_hrs = self.week.needed_hours()[sst.employee]
            if wk_needed_hrs < self.shift.hours:
                return "NA"
            if not self.employee:
                self.__setattr__('employee', sst.first().employee)
                print(f'Employee set to {sst.first().employee.name} via @set_sst')
                return "ASSIGNED"
        
        
        
        return
    def save (self, *args, **kwargs):
        self._save_empl_sentiment ()
        super().save(*args, **kwargs)
        self.post_save()
    def post_save (self):
        self.conflicting_slots.set(self._get_conflicting_slots() )
        self.fillableByN = self._fillableBy().count()
    def url (self):
        return self.workday.url() + f"{self.shift.name}/"
    def _save_empl_sentiment (self):
        #fill in employee from template
        if ShiftPreference.objects.filter(employee=self.employee,shift=self.shift):
            sc = { -2:0,   -1:25,   0:50,   1:75,   2:100 }
            self.empl_sentiment = sc[ShiftPreference.objects.filter(employee=self.employee,shift=self.shift).first().score]
        else:
            self.empl_sentiment = 50
        if self.is_turnaround :
            self.empl_sentiment -= 35
        if self.is_preturnaround :
            self.empl_sentiment -= 35
        if self.isOverStreakPref:
            self.empl_sentiment -= 20
        if self.shouldBeTdo:
            self.empl_sentiment = 0
        
    objects      = SlotManager.as_manager()
    turnarounds  = TurnaroundManager.as_manager()
# ============================================================================
class ShiftTemplate (models.Model) :
    """
    Fields:
            -  shift
            -  employee
            -  ppd_id 
    """
    # fields: name, start, duration 
    shift       = models.ForeignKey(Shift, on_delete=models.CASCADE)
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    ppd_id      = models.IntegerField()

    def weekAB(self):
        return 'A' if self.ppd_id < 7 else 'B'
    
    @property
    def weekday (self):
        days = "Sun Mon Tue Wed Thu Fri Sat".split()
        return days[self.ppd_id % 7]

    @property
    def iweekday (self):
        return self.ppd_id % 7

    def __str__(self) :
        return f'{self.shift.name} Template'

    @property
    def url(self):
        return reverse("shifttemplate", kwargs={"pk": self.pk})
    
    
    def __str__(self) :
        return f'{self.weekday}{self.weekAB()}:{self.shift.name} Template'

    class Meta:
        unique_together = ['shift', 'ppd_id']
# ============================================================================
class TemplatedDayOff (models.Model) :
    """
    Fields:
        -  employee
        -  sd_id (0-41) 
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    ppd_id   = models.IntegerField (null=True) 
    sd_id    = models.IntegerField ()
    
    @property
    def symb (self) :
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZБДЖИЛФШЮЯΔΘΛΞΣΨΩ"[self.sd_id]

    def weekAB (self):
        if self.sd_id == None:
            return 'G'
        return  'A' if self.ppd_id < 7 else 'B'
    
    def weekday (self):
        days = "Sun Mon Tue Wed Thu Fri Sat".split(" ")
        return days[self.ppd_id % 7]
    
    def __str__ (self) :
        return f'TDO-{self.symb}'
    
    class Meta:
        unique_together = ['employee','sd_id']
# ============================================================================
class PtoRequest (ComputedFieldsModel): 
    employee         = models.ForeignKey (Employee, on_delete=models.CASCADE)
    workday          = models.DateField (null=True, blank=True)
    dateCreated      = models.DateTimeField (auto_now_add=True)
    status           = models.CharField (max_length=20, choices=PTO_STATUS_CHOICES, default='P')
    manager_approval = models.BooleanField (default=False)
    sd_id            = models.IntegerField (default=-1)
    #stands_respected = models.BooleanField(default=True)

    @computed (models.BooleanField(), depends=[('self',['status'])])
    def stands_respected (self) -> bool:
        if Slot.objects.filter(workday__date=self.workday, employee=self.employee).count() > 0:
            return False
        return True

    def __str__(self) :
        # ex: "<JOSH PTOReq: Sep5>"
        return f'<{self.employee} PTOReq>'
    @property
    def headsUpLength (self):
        return (self.workday.date - self.dateCreated).days
    
    @property
    def days_away (self):
        return (self.workday.date - dt.date.today()).days
    
    def save (self, *args, **kwargs):
        if self.sd_id == -1:
            self.sd_id = Workday.objects.get(date=self.workday).sd_id
        super().save(*args, **kwargs)
# ============================================================================
class SlotPriority (models.Model):
    iweekday = models.IntegerField()
    shift    = models.ForeignKey(Shift, on_delete=models.CASCADE)
    priority = models.CharField(max_length=20, choices=PRIORITIES, default='M')

    class Meta:
        unique_together = ['iweekday', 'shift']     
# ============================================================================
class ShiftPreference (ComputedFieldsModel):
    """SHIFT PREFERENCE [model]
    >>> employee <fkey> 
    >>> shift    <fkey>
    >>> priority <str> SP/P/N/D/SD
    >>> score    <int> -2/-1/0/1/2
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift    = models.ForeignKey(Shift, on_delete=models.CASCADE)
    priority = models.CharField(max_length=2, choices=PREF_SCORES, default='N')

    @computed (models.IntegerField(), depends=[('self',['priority'])])
    def score (self):
        scoremap = { 'SP':2, 'P':1, 'N':0, 'D':-1, 'SD':-2 }
        return scoremap[self.priority]

    class Meta:
        unique_together = ['employee', 'shift']
        
    def __str__ (self):
        return f'<{self.employee} {self.shift}: {self.priority}>'
    
    objects = ShiftPreferenceManager.as_manager()
# ============================================================================
class SchedulingMax (models.Model):
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE)
    year       = models.IntegerField()
    pay_period = models.IntegerField(null=True, blank=True)
    max_hours  = models.IntegerField()
    
    class Meta:
        unique_together = ('employee', 'year', 'pay_period')


def generate_schedule (year,number):
    yeardates = []
    for date in SCH_STARTDATE_SET:
        if date.year == year:
            yeardates.append(date)
    yeardates.sort()
    n = Schedule.objects.filter(year=year,number=number).count()
    version = "ABCDEFGHIJKLMNOPQRST"[n]
    print(yeardates)
    start_date = yeardates[number - 1]
    sch = Schedule.objects.create(start_date=start_date, version=version, number=number, year=year)
    sch.save()
    
    for slot in sch.slots.all():
        slot.save()
    
        

def tally (lst):
    """ TALLY A LIST OF VALUES 
    Tallys each occurence of a particular value"""
    tally = {}
    for item in lst:
        if item in tally:
            tally[item] += 1
        else:
            tally[item] = 1
    return tally

def sortDict (d):
    """ SORT DICT BY VALUE """
    return {k: v for k, v in sorted(d.items(), key=lambda item: item[1])}

def dayLetter (i):
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZБДЖИЛФШЮЯΔΘΛΞΣΨΩ"


