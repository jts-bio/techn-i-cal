import datetime as dt
from re import sub
import random
from django.http import JsonResponse
from django.urls import reverse_lazy

from computedfields.models import ComputedFieldsModel, computed
from django.db import models
from django.db.models import Deferrable
from django.db.models import (Avg, Count, DurationField, ExpressionWrapper, F,
                              FloatField, Max, Min, OuterRef, Q, QuerySet,
                              StdDev, Subquery, Sum, Variance)
from django.db.models.functions import Coalesce
from django.urls import reverse
from taggit.managers import TaggableManager
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
SCH_STARTDATE_SET       = [(TEMPLATESCH_STARTDATE + dt.timedelta(days=42*i)) for i in range (50)]
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
                    ('Pending', 'Pending'),
                    ('Approved', 'Approved'),
                    ('Denide', 'Denied'),
                )


def YEAR_SCHDATES (year):
    all_ = [TEMPLATESCH_STARTDATE + dt.timedelta(days=i*42) for i in range(-100,100)]
    inYear = []
    for d in all_:
        if d.year == year:
            inYear.append(d)
    return inYear

#*--------------------------------*#
#* --- ---    MANAGERS    --- --- *#
#*--------------------------------*#
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
    def empty           (self):
        return self.filter(employee=None)
    def filled          (self):
        return self.exclude(employee=None)
    def on_workday      (self, workday):
        return self.filter(workday=workday)
    def ShiftDetail     (self, workday, shift):
        if self.filter(workday=workday, shift=shift).exists():
            return self.filter(
                workday=workday, 
                shift=shift).annotate(
                                employee= F('employee__name'),
                                workday= F('workday__date')
                            )
    
    def empls_weekly_hours (self, year, week, employee):
        return self.filter(
            workday__iweek= week,
            workday__date__year= year,
            employee= employee
            ).aggregate(hours=Sum('shift__hours'))
    def turnarounds     (self):
        turnarounds = []
        for i in self.all():
            if i.is_turnaround:
                turnarounds.append(i.pk)
        return self.filter(pk__in=turnarounds)
    def preturnarounds  (self):
        preturnarounds = []
        for i in self.all():
            if i.is_preturnaround:
                preturnarounds.append(i.pk)
        return self.filter(pk__in=preturnarounds)
    def unfavorables    (self):
        ufs = [i.pk for i in self if i.is_unfavorable() == True]
        return Slot.objects.filter(pk__in=ufs)
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
    def streaks         (self, employee):
        return self.filter(employee=employee, is_terminal=True)
    def unusual_fills (self):
        """"""
        return self.exclude(employee=None).exclude(template_employee=None).exclude(employee=F('template_employee'))
    def unusualFills    (self):
        unusual = []
        ssts = ShiftTemplate.objects.all()
        slots = self.filter(shift=Subquery(ssts.values('shift')), workday__sd_id=Subquery(ssts.values('sd_id'))).exclude(employee=None)
        for sst in ssts:
            if self.filter(workday__sd_id=sst.sd_id, shift=sst.shift).exists():
                if not self.filter(employee=None).exists():
                    if not self.filter(employee=sst.employee):
                        unusual.append(slots.filter(shift=sst.shift).first())
        return self.filter(pk__in=[i.pk for i in unusual])
    def sch__pmSlots    (self, year, sch):
        return self.objects.filter(workday__date__year=year,workday__ischedule=sch, shift__start__hour__gte=12)
    def tdoConflicts    (self):
        conflicts = []
        for i in self:
            if i.shouldBeTdo:
                conflicts += [i.pk]
        return self.filter(pk__in=conflicts)
    def tally_schedule_streaks (self, employee, year, schedule):
        return tally(list(self.filter(employee=employee, is_terminal=True, workday__date__year=year, workday__ischedule=schedule).values_list('streak')))    
    def evenings (self):
        return self.filter(shift__start__gte=dt.time(12,0,0))
                
class TurnaroundManager (models.QuerySet):
    def schedule (self, year, number):
        sch = Schedule.objects.get(year=year,number=number)
        return Slot.objects.filter(workday__schedule=sch)
# ============================================================================
class EmployeeManager (models.QuerySet): 
    def low_option_emps (self):
        return self.filter (fte__gt=0, n_trained__lte=3)
    def prn_employees (self):
        return self.filter(fte=0)
    def weekly_hours (self, year, week):
        return Employee.objects.annotate(
                hours=Sum(Subquery(Slot.objects.filter(workday__date__year=year,workday__iweek=week, employee=F('pk')).aggregate(hours=Sum(F('shift__hours')))))
            )
    def evening_employees (self):
        return self.filter(time_pref='Evening')
    def full_template_employees (self):
        return self.template_ratio().filter(template_ratio=1)
    def template_hours(self):
        return self.annotate(
                    template_hours=Subquery(
                        ShiftTemplate.objects.filter(
                            employee=OuterRef('pk')
                        ).values('shift__hours').annotate(
                    template_hours=Sum('shift__hours')
                        ).values('template_hours')
                    )
                )
    def fte_schedule_hours (self):
        return self.annotate(
                fte_schedule_hours=F('fte') * 240
            )
    def template_ratio (self):
        return self.template_hours().fte_schedule_hours().annotate(
                template_ratio=F('template_hours')/F('fte_schedule_hours')
            )
    def emusr_employees (self):
        """
        EMUSR employees are those that have the properties to be required 
        to fill a certain amount of Unpreferable Shifts per schedule. 
        
        They will have these properties:
            - not Evening Employees
            - Less than 80% of their shifts in a schedule are not templated in advance
            - They are not PRN employees
        """
        return self.template_ratio().filter(template_ratio__lte=0.8)
    def in_slot (self, shift, workday):
        return self.filter(slot__shift__name=shift, slot__workday=workday)
    def in_other_slot (self, shift, workday):
        e = Slot.objects.filter(workday=workday).exclude(shift=shift).values('employee')
        return self.filter(pk__in=e)
    def can_fill_shift_on_day (self, shift,cls, workday, method="available"):
        shift = Shift.objects.get(name=shift,cls=cls)
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
class PtoRequestManager (models.QuerySet):
    """ Model Manager for :model:`sch.PtoRequest` """
    def violated (self):
        violatedRequests = []
        for ptor in self:
            if Slot.objects.filter(employee=ptor.employee, workday__date=ptor.workday).exists() == True:
                violatedRequests.append(ptor)
        return self.filter(pk__in=[ptor.pk for ptor in violatedRequests])
    def conflicts (self, scheduleVersion):
        return PtoRequest.objects.annotate(
                conflicts=Subquery(
                    Slot.objects.filter(
                        schedule__version=scheduleVersion,
                        employee=OuterRef('employee'),
                        workday__date=OuterRef('workday')
                    ).annotate(
                        count=Sum(1)
                    ).values('count')
                )
        )

#************************************#
#* --- ---      MODELS      --- --- *#
#************************************#
# ============================================================================

class Shift (models.Model) :
    """
    model <<< SHIFT >>>
    
        hours               ---> 10.0
        on_days_display     ---> "Sun Mon Tue Wed Thu Fri Sat"
        ppd_ids             ---> 0,1,2,3,4,5,6,7,8,9,10,11,12,13
        
    
    """
    # fields: name, start, duration 
    name            = models.CharField (max_length=100)
    cls             = models.CharField (max_length=20, choices=(('CPhT','CPhT'),('RPh','RPh')), null=True)
    start           = models.TimeField()
    duration        = models.DurationField()
    hours           = models.FloatField() # audo set on save
    group           = models.CharField(max_length=10, choices=(('AM','Morning'),('MD','Midday'),('PM','Evening'),('XN','Overnight')), null=True)
    occur_days      = MultiSelectField (choices=DAYCHOICES, max_choices=7, max_length=14, default=[0,1,2,3,4,5,6])
    is_iv           = models.BooleanField (default=False)

    class Meta: 
        
        ordering = ['start']
        
    def save (self, *args, **kwargs):
        if self.hours == None:
            self.hours = self._set_hours()
        super().save(*args, **kwargs)
    def __str__(self) :
        return self.name
    def url(self):
        return reverse("sch:shift-detail", kwargs={"cls":self.cls, "name": self.name})
    def url__template(self):
        return reverse('sch:shift-template-view', args=[self.pk])
    def url__tallies (self):
        return reverse('sch:shift-tallies-view', args=[self.pk])
    def prevUrl (self): 
        """Get the url of the shift with the next lowest pk. If my pk is lowest, return my url."""
        prev = Shift.objects.filter(cls=self.cls).filter(pk__lt=self.pk).order_by('-pk').first()
        if prev:
            return prev.url()
        return self.url()
    def nextUrl (self):
        """Get the url of the shift with the next highest pk. If my pk is highest, return my url."""
        next = Shift.objects.filter(cls=self.cls).filter(pk__gt=self.pk).order_by('pk').first()
        if next:
            return next.url()
        return self.url()
    def _set_hours (self):
        return self.duration.total_seconds() / 3600 - 0.5
    @property
    def ppd_ids (self):
        """
        Returns a list of the ids of the PPDs (0-13) that this shift occurs on.
        """
        ids = list(self.occur_days)
        for i in self.occur_days:
            ids.append(str(int(i)+7))
        return ids
    @property
    def sd_ids (self):
        """
        """
        ids = list(self.occur_days)
        for i in self.occur_days:
            for x in [7,14,21,28,35]:
                ids.append(int(i)+x)
        return ids
    def end (self):
        return (dt.datetime(2022,1,1,self.start.hour,self.start.minute) + self.duration).time()
    def avgSentiment (self):
        sp = ShiftPreference.objects.filter(shift=self).values('score')
        if sp:
            return sum(sp)/len(sp)
        

    objects = ShiftManager.as_manager()
# ============================================================================
class Employee (models.Model) :
    # fields: name, fte_14_day , shifts_trained, shifts_available 
    name            = models.CharField (max_length=100)
    fte_14_day      = models.FloatField(default=80)
    fte             = models.FloatField(default=1)
    shifts_trained  = models.ManyToManyField (Shift, related_name='trained')
    shifts_available= models.ManyToManyField (Shift, related_name='available')
    streak_pref     = models.IntegerField (default=3)
    trade_one_offs  = models.BooleanField (default=True)
    cls             = models.CharField (choices=(('CPhT','CPhT'),('RPh','RPh')),default='CPhT',blank=True, null=True,max_length=20)
    evening_pref    = models.BooleanField (default=False)
    time_pref       = models.CharField(max_length=10, choices=(('AM','Morning'),('MD','Midday'),('PM','Evening'),('XN','Overnight')))
    slug            = models.CharField (primary_key=True ,max_length=25,blank=True)
    hire_date       = models.DateField (default=dt.date(2018,4,11))
    
    
    class Meta:
        ordering    = ['cls', 'name']

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fte = self.fte_14_day / 80
    def url__tallies (self):
        return reverse("sch:employee-shift-tallies", kwargs={"empId":self.pk})
    def url__update (self):
        return reverse("sch:employee-update", kwargs={"name":self.name})
    @property
    def yrs_experience (self):
        return round((TODAY - self.hire_date).days / 365, 2)
    def __str__(self) :
        return self.name
    # computed fields:
    def _set_fte (self):
        return self.fte_14_day / 80
    def url(self):
        return reverse("sch:v2-employee-detail", kwargs={"empId": self.pk})
    def weekHours (self, wd):
        return wd.week.slots.filter(employee=self).aggregate(hours=Sum('shift__hours'))['hours']
    def periodHours (self, wd):
        return wd.period.slots.filter(employee=self).aggregate(hours=Sum('shift__hours'))['hours']
    def weekly_hours (self, year, iweek):
        return Slot.objects.filter(workday__date__year=year,workday__iweek=iweek, employee=self).aggregate(hours=Sum('shift__hours'))['hours']
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
    def favorable_shifts (self):
        if self.evening_pref:
            return self.shifts_available.filter(start__hour__gt=10)
        if not self.evening_pref:
            return self.shifts_available.filter(start__hour__lte=10)
    @property
    def get_TdoSlotConflicts (self):
        tdos = list(TemplatedDayOff.objects.filter(employee=self).values_list('pk',flat=True))
        return Slot.objects.filter(workday__sd_id__in=tdos, employee=self)
    def get_WeeklyHours (self, weekId):
        return sum(list(Slot.objects.filter(employee=self, week__pk=weekId).values_list('shift__hours')))
    def info_printWeek(self,year,week):
            slots = list(Slot.objects.filter(employee=self,workday__date__year=year,workday__iweek=week).values_list('shift__name',flat=True))
            return f'{self.name}: {slots}'
    def schedule_data (self, schId):
        sch = Schedule.objects.get(slug=schId)
        empl_schedule = {}
        for wd in sch.workdays.all():
            emplSlot = wd.slots.filter(employee=self)
            if emplSlot.exists():
                empl_schedule[wd] = emplSlot.first()
            else:
                empl_schedule[wd] = None
        return empl_schedule
    def save (self, *args, **kwargs):
        slugString = self.name.strip().replace(" ","-")
        self.slug      = slugString
        if self.fte == None or self.fte == 0:
            self.fte = self._set_fte()
        super().save()
        
    
       
    objects = EmployeeManager.as_manager()
# ============================================================================
class Workday (models.Model) :
    # fields: date, shifts 
    date     = models.DateField()
    week     = models.ForeignKey("week",     on_delete=models.CASCADE, null=True, related_name='workdays')
    period   = models.ForeignKey("Period",   on_delete=models.CASCADE, null=True, related_name='workdays')
    schedule = models.ForeignKey("Schedule", on_delete=models.CASCADE, null=True, related_name='workdays')
    slug     = models.CharField   (max_length=30, null=True, blank=True)
    iweekday = models.IntegerField(default=-1)
    iweek    = models.IntegerField(default=-1)
    iperiod  = models.IntegerField(default=-1)
    ischedule= models.IntegerField(default=-1)
    ppd_id   = models.IntegerField(default=-1)
    sd_id    = models.IntegerField(default=-1)  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.slug = self.date.strftime("%Y-%m-%d") + self.schedule.version
        self.sd_id= (self.date - TEMPLATESCH_STARTDATE).days % 42
        actions = self.Actions()
        actions._set_iperiod(self)
        actions._set_iweek(self)
        actions._set_iweekday(self)
        actions._set_ppd_id(self)
        actions._set_sd_id(self)
        actions._set_slug(self)
        actions._set_slugid(self)
    __all__ = ['date','slug','iweekday','iweek','iperiod','ppd_id','weekday',
               'shifts',
               'filledSlots','n_slots',"n_emptySlots",'n_shifts','percFilled',
               'siblings_iweek']
    
    @property 
    def pto (self):
        return PtoRequest.objects.filter(workday=self.date)
    class Actions :
        def _set_slug (self,instance) : 
            return instance.date.strftime('%Y-%m-%d')
        def _set_slugid (self,instance) :
            return instance.schedule.slug + instance.date.strftime('%Y-%m-%d') 
        def _set_iweekday (self,instance) :
            # range 0 -> 6
            val = int (instance.date.strftime('%w'))
            instance.__setattr__('iweekday',val)
        def _set_iweek (self,instance) :
            # range 0 -> 53
            val = int (instance.date.strftime('%U'))
            instance.__setattr__('iweek',val)
        def _set_iperiod (self,instance) :
            # range 0 -> 27
            val = int (instance.date.strftime('%U')) // 2
            instance.__setattr__('iperiod',val)
        def _set_ppd_id (self,instance) :
            # range 0 -> 13
            val = (instance.date - TEMPLATESCH_STARTDATE).days % 14   
            instance.__setattr__('ppd_id',val)
        def _set_ischedule (self,instance) :
            # range 0 -> 9
            val = self.schedule.number
            instance.__setattr__('ppd_id',val) 
        def _set_sd_id  (self,instance) :
            # range 0 -> 41
            val = (instance.date - TEMPLATESCH_STARTDATE).days % 42
            instance.__setattr__('sd_id',val)
        def _set_ppd_id  (self,instance) :
            # range 0 -> 41
            val = (instance.date - TEMPLATESCH_STARTDATE).days % 14
            instance.__setattr__('ppd_id',val)
    @property
    def weekday (self): 
        # Sun -> Sat
        return self.date.strftime('%A')
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
    def percFilled (self) :
        return self.filledSlots.count() / self.shifts.count()
    def percent (self):
        decimal = self.slots.filled().count() / self.slots.all().count()
        return int(decimal * 100)
    def url (self) :
        return reverse("workday", kwargs={"sch": self.schedule.pk,"slug": self.slug})
    def prevWD (self) :
        sd = self.sd_id 
        if sd != 0:
            return self.schedule.workdays.filter(sd_id=sd-1).first()
        else :
            return None
    def nextWD (self) :
        sd = self.sd_id
        if sd != 41:
            return self.schedule.workdays.filter(sd_id=sd+1).first()
        else :
            return None
    def prevURL (self) :
        return self.prevWD().url()
    def nextURL (self) :
        return self.nextWD().url()
    @property
    def days_away           (self) :
        td = self.date - TODAY 
        return td.days
    def related_slots       (self) :
        return Slot.objects.filter(workday=self)
    @property
    def n_unfilled          (self) :
        return  self.n_shifts - self.related_slots().count()
    @property
    def list_unpref_slots   (self):
        return self.filledSlots.annotate(
                score=Subquery(ShiftPreference.objects.filter(employee=OuterRef('employee'),shift=OuterRef('shift')).values('score'))
            ).filter(score__lt=0)
    @property
    def areTemplateSlotsFilled (self):
        tslots = ShiftTemplate.objects.filter(sd_id=self.sd_id).values_list('shift',flat=True)
        for shift in tslots:
            if not self.filledSlots.filter(shift=shift).exists():
                return False
        return True
    @property
    def printSchedule   (self):
        for slot in self.slots.all() :
            print(slot.shift, slot.employee)
    def hours           (self):
        return Employee.objects.all().annotate(hours=Subquery(self.slots.exclude(employee=None).values('hours')))
    def free_today (self):
        alreadyWorking = self.slots.values('employee')
        tdos = TemplatedDayOff.objects.filter(sd_id=self.sd_id).values('employee')
        ptoRequested = self.pto().values('employee')
        exempts = Employee.objects.filter(pk__in=alreadyWorking).union(
                    Employee.objects.filter(pk__in=tdos)).union(
                    Employee.objects.filter(pk__in=ptoRequested)).values('pk')
        return Employee.objects.all().exclude(pk__in=exempts)
    def who_can_fill    (self, shift):
        if shift not in self.shifts:
            return None
        if Slot.objects.filter(workday=self,shift=shift).exists():
            current = Slot.objects.get(workday=self,shift=shift).employee
            return Employee.objects.can_fill_shift_on_day(
                workday=self,shift=shift) | Employee.objects.filter(
                    pk=current.pk)
        return Employee.objects.can_fill_shift_on_day(workday=self,shift=shift)
    def n_can_fill      (self, shift):
        if self.who_can_fill == None:
            return None 
        return len (self.who_can_fill(shift))
    def template_exceptions (self):
        templates = ShiftTemplate.objects.filter(sd_id=self.sd_id)
        ptoReqs   = PtoRequest.objects.filter(workday=self.date)
        excepts = []
        for templ in templates:
            if ptoReqs.filter(employee=templ.employee).exists():
                excepts.append(templ)
        return excepts
    def wkd             (self):
        return self.weekday[:3]
    def pto             (self):
        return PtoRequest.objects.filter(workday=self.date)
    def tdo             (self):
        return TemplatedDayOff.objects.filter(sd_id=self.sd_id)
    def on_deck         (self):
        not_on_deck = []
        if self.pto().exists(): 
            not_on_deck += [pk for pk in self.pto().values_list('employee__pk',flat=True)]
        if self.tdo().exists():
            not_on_deck += [pk for pk in self.tdo().values_list('employee__pk',flat=True)]
        onDay = list(self.slots.values_list('employee',flat=True))
        not_on_deck += onDay
        print(not_on_deck)
        return Employee.objects.all().exclude(pk__in=not_on_deck)
    def save            (self, *args, **kwargs) :
        self.slug = self.date.strftime('%Y-%m-%d') + self.schedule.version
        self.sd_id = (self.date - TEMPLATESCH_STARTDATE).days % 42
        super().save(*args,**kwargs)
        self.post_save()
    def post_save       (self):
        for i in self.shifts:
            if not Slot.objects.filter(workday=self,shift=i).exists():
                s = Slot.objects.create(workday=self,shift=i,week=self.week,period=self.period,schedule=self.schedule)
                s.save()
    def url             (self):
        return reverse('sch:v2-workday-detail', args=[self.slug])
    def url_tooltip     (self):
        return f'/sch/{self.slug}/get-tooltip/'
    def __str__         (self) :
        return str(self.date.strftime('%Y %m %d'))
    
    objects = WorkdayManager.as_manager()
# ============================================================================  
class Week (models.Model) :
    __all__ = [
        'year','iweek','prevWeek','nextWeek',
    ]
    
    iweek       = models.IntegerField (null=True, blank=True) 
    year        = models.IntegerField (null=True, blank=True)
    number      = models.IntegerField (null=True, blank=True)
    period      = models.ForeignKey   ("Period", on_delete=models.CASCADE,   null=True,related_name='weeks')
    schedule    = models.ForeignKey   ("Schedule", on_delete=models.CASCADE, null=True,related_name='weeks')
    start_date  = models.DateField    (blank=True, null=True)
    
    class Meta:
        ordering = ['year','number','schedule__version']
    def ACTION__clearAllSlots (self):
        slots = self.slots.filled()
        slots.update(employee=None)
    def URL__clearAllSlots (self):
        return reverse('clearAllSlots', kwargs={'week': self.pk})
    def total_overtime (self):
        overtime = 0
        for employee in Employee.objects.all():
            hrs = sum(list(self.slots.filter(employee=employee).values_list('shift__hours',flat=True)))
            if hrs > 40:
                ot_hrs = hrs - 40
            else:
                ot_hrs = 0
            overtime += ot_hrs
        return overtime 
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
        if int(str(empl.fte_14_day / 2)[-1]) == 5:
            otherWeek = self.period.weeks.exclude(pk=self.pk).filter(slots__employee=empl,slots__filled=True)
            owslots = otherWeek.slots.filter(employee=empl).aggregate(Sum('shift__hours'))['shift__hours__sum']
        else:
            owslots = 0
        needed = empl.fte_14_day / 2
    
        if owslots > (empl.fte_14_day / 2):
            needed = needed - 5
        else: 
            needed = needed + 5   
        if needed > 40:
            needed = 40         
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
        return sortDict(output,reverse=True)
    def total_hours(self):
        # Calculate the total hours for each employee
        data = self.slots.values('employee').annotate(hours=Sum('shift__hours'))
        # Define a subquery to get the total hours for each employee
        total_hours_subquery = data.filter(employee=OuterRef('pk')).values('hours')
        # Annotate the Employee queryset with the total hours for each employee
        employees = Employee.objects.annotate(hours=Subquery(total_hours_subquery))
        return employees
    def empl_with_max_needed_hours (self):   
        return self.needed_hours()[0]
    def nFilled (self):
        return self.slots.filter(employee__isnull=False).count()
    def nEmpty (self):
        return self.slots.filter(employee__isnull=True).count()
    def percent (self):
        return int((self.slots.filled().count() / self.slots.all().count()) * 100)
    @property
    def dates (self):
        return [self.start_date + dt.timedelta(days=i) for i in range(7)]  
    @property
    def slug (self) : 
        return f'{self.year}_{self.number}'
    @property
    def name     (self) : 
        return f'{self.year}_{self.iweek}'   
    def prevWeek (self) :
        prev_week = self.schedule.weeks.filter(number=self.number - 1)
        if prev_week.exists():
            return prev_week.first()
        else:
            return self  
    def nextWeek (self) :
        next_week = self.schedule.weeks.filter(number=self.number + 1)
        if next_week.exists():
            return next_week.first()
        else:
            return self
    @property
    def slots    (self) :
        dates = self.dates
        return Slot.objects.filter(workday__date__in=dates)
    def n_options_for_slots (self):
        possibles = []
        for s in self.slots.all():
            possibles += s._fillableBy()
        return sortDict (tally (possibles))    
    def _print_fillByInfo (self):
        for s in self.slots.empty():
            print (s.shift.name,s.workday.date,[(i.name,s.week.empl_needed_hrs(i)) for i in s._fillableBy()])      
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
    def url (self): 
        return reverse('sch:v2-week-detail',kwargs={
                                            'week': self.pk
                                        })
    def tpl_fill_url (self):
        return f'/sch/weeksolve/{self.id}/solve/fill-templates/'
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
        return reverse('sch:period-detail', args=[self.pk])
    def url__fill_one_with_best (self):
        pass  
    def __str__ (self):
        return f'PayPeriod {self.year}.{self.number}.{self.schedule.version}'
    def empl_needed_hrs (self,empl):
        slots = self.slots.filter(employee=empl)
        wds = slots.values('workday__date')
        hrs   = slots.aggregate(Sum('shift__hours'))['shift__hours__sum']
        if hrs is None:
            hrs = 0
        needed = empl.fte_14_day 
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
        return sortDict(output,reverse=True)
    def percent (self):
        return int((self.slots.filled().count() / self.slots.all().count()) * 100)
    class FillActions:
        def fill_slot_with_lowest_hour_employee (self):
            empl = self.needed_hours.keys()[0]
            fillableSlots = []
            for emptySlot in self.slots.filter(employee=None):
                if empl in emptySlot.fillable_by():
                    fillableSlots += [emptySlot]
            selectedSlot = fillableSlots[random.randint(0,len(fillableSlots))]
            
            selectedSlot._set_employee(empl)
            if selectedSlot.employee != None:
                return "SUCCESS: FILLED VIA PayPeriod.FillActions.fill_slot_with_lowest_hour_employee"
# ============================================================================  
class Schedule (models.Model):
    year       = models.IntegerField(null=True,default=None)
    number     = models.IntegerField(null=True,default=None)
    start_date = models.DateField()
    status     = models.IntegerField(choices=list(enumerate("working,finished,discarded")),default=0)
    version    = models.CharField(max_length=1,default='A')
    slug       = models.CharField(max_length=20,default="")
    

    class Meta :
        ordering = ['year','number','version']
    
    def save (self, *args, **kwargs) :
        if self.year    == None :
            self.year   = self.start_date.year
        if self.number  == None :
            self.number = int (self.start_date.strftime("%U")) // 6
        if self.slug    == "":
            self.slug   = f'{self.year}-S{self.number}{self.version}'
        super().save(*args, **kwargs)
        self.post_save()
    def post_save (self) :
        for pp in self.payPeriod_start_dates:
            if not Period.objects.filter(start_date=pp,schedule=self).exists():
                p = Period.objects.create(start_date=pp,year=pp.year,number=int(pp.strftime("%U"))//2,schedule=self)
                p.save()
    def percent (self):
        return int((self.slots.filled().count() / self.slots.all().count()) * 100)
    @property
    def week_start_dates (self):
        return [self.start_date + dt.timedelta(days=i*7) for i in range(6)]
    @property
    def payPeriod_start_dates (self):
        return [self.start_date + dt.timedelta(days=i*14) for i in range(3)]             
    def url     (self) :
        url = reverse('sch:v2-schedule-detail',  kwargs={'schId':self.slug})
        return url
    def url__solve  (self):
        return reverse('sch:v2-schedule-solve',  kwargs={'schId':self.slug})
    def url__solve_b    (self):
        return reverse('sch:v2-schedule-solve-alg2', kwargs={'schId':self.slug})
    def url__clear  (self):
        return reverse('sch:v2-schedule-clear',  kwargs={'schId':self.slug})
    def url__previous (self):
        if self.number == 1:
            return Schedule.objects.filter(year=self.year-1,version=self.version).first()
        return Schedule.objects.get(year=self.year,number=self.number-1,version=self.version)
    def url__next   (self):
        if self.number == Schedule.objects.filter(year=self.year,version=self.version).last():
            return Schedule.objects.filter(year=self.year+1,version=self.version).first()
        return Schedule.objects.get(year=self.year,number=self.number+1,version=self.version)
    def __str__     (self):
        return f"{self.year}-S{self.number}{self.version}"
    def unfavorableRatio (self,employee):
        slots = self.slots.filter(employee=employee)
        if slots.count() == 0:
            return 0
        unfavorable = self.slots.filter(employee=employee,shift__in=employee.unfavorable_shifts())
        return unfavorable.count()/slots.count()
    def repr_status     (self):
        return ["Working Draft","Final","Discarded"][self.status]
    @property
    def pto_requests (self):
        return PtoRequest.objects.filter(workday__in=self.workdays.all().values('date'))
    def pto_percent (self):
        if self.pto_requests.count() == 0:
            return 0
        return 100 - int(self.pto_conflicts().count() / self.pto_requests.count() * 100)
    def pto_conflicts (self):
        """PTO CONFLICTS 
        List of Slots ---> Employee has Pto on this day"""
        conflicts = []
        for pto in self.pto_requests:
            if self.slots.filter(employee=pto.employee, workday__sd_id=pto.sd_id).exists():
                conflicts += [self.slots.filter(employee=pto.employee, workday__sd_id=pto.sd_id).first()]
        return self.slots.filter(pk__in=[c.pk for c in conflicts])
    def as_empl_dict (self):
        all_schedules = {} 
        for empl in Employee.objects.all():
            empl_schedule = []
            for wd in self.workdays.all():
                assignment = wd.slots.filter(employee=empl)
                if assignment.exists():
                    empl_schedule += [wd.slots.filter(employee=empl).first()]
                elif self.pto_requests.filter(employee=empl,workday=wd.date).exists():
                    empl_schedule += ["PTO"]
                else:
                    empl_schedule += [None]
            all_schedules[empl] = empl_schedule
        return all_schedules
    def as_shift_dict (self):
        all_schedules = {}
        for shift in Shift.objects.all():
            shift_schedule = []
            for wd in self.workdays.all():
                assignment = wd.slots.filter(shift=shift)
                if assignment.exists():
                    shift_schedule += [wd.slots.get(shift=shift)]
                else:
                    shift_schedule += [None]
            all_schedules[shift] = shift_schedule
        return all_schedules
    class Actions :
        def fillTemplates (self,instance,**kwargs):
            print (f'===============================')
            print (f'[ACTION : SCHEDULE__FILLTEMPLATES] {dt.datetime.now()}')
            for slot in instance.slots.all():
                if slot.employee is None:
                    if slot.template_employee is not None:
                        slot.siblings_day.filter(employee=slot.template_employee).update(employee=None)
                        if PtoRequest.objects.filter(employee=slot.template_employee,workday=slot.workday.date).exists():
                            print('Slot Templating Skipped due to PTO Request')
                        else:
                            slot.employee = slot.template_employee
                            slot.save()
                            print (f'Filled Slot {slot.workday.date.month}-{slot.workday.date.day} {slot.shift}: with {slot.employee} via Template')
            
            print (f'FINISHED TEMPLATED SHIFT ASSIGNMENTS {dt.datetime.now()}')
            print (f'===============================')
        def fillSlots (self,instance):
            print (f'STARTING SCHEDULE FILL: {dt.datetime.now()}')
            self.fillTemplates(instance)
            for i in range(700):
                slot = instance.slots.empty()[random.randint(0,instance.slots.empty().count()-1)]
                slot.fillWithBestChoice()
                print(f'Filled Slots {slot.workday.date.month}-{slot.workday.date.day} {slot.shift}: with {slot.employee}')
            print(f'Schedule-Wide Solution Completed at {dt.datetime.now()}')  
        def solveOmap (self,instance):
            keeptrying = 300
            while keeptrying > 0:
                slot = instance.slots.empty()[random.randint(0,instance.slots.empty().count()-1)]
                omap = slot.createOptionsMap()
                if omap['can'].exists():
                    n = random.randint(0,len(omap['can'])-1)
                    emp = omap['can'][n]
                    slot.employee = emp 
                    slot.save()
                    keeptrying -= 1
                    print(f'SLOT {slot} FILLED {dt.datetime.now()} VIA OPTION-MAPPING ALGORITHM -- E_WK_HRS={sum(list(slot.week.slots.filter(employee=slot.employee).values_list("shift__hours",flat=True)))} ')
        def deleteSlots (self,instance):
            instance.slots.all().update(employee=None)
# ============================================================================
class Slot (models.Model) :
    # fields: workday, shift, employee
    workday        = models.ForeignKey ("Workday",  on_delete=models.CASCADE, null=True, related_name='slots')
    shift          = models.ForeignKey ("Shift",    on_delete=models.CASCADE, null=True, related_name='slots')
    employee       = models.ForeignKey ("Employee", on_delete=models.CASCADE, null=True, related_name='slots')
    week           = models.ForeignKey ("Week",     on_delete=models.CASCADE, null=True, related_name='slots')
    period         = models.ForeignKey ("Period",   on_delete=models.CASCADE, null=True, related_name='slots')
    schedule       = models.ForeignKey ("Schedule", on_delete=models.CASCADE, null=True, related_name='slots')
    empl_sentiment = models.SmallIntegerField   (null=True, default=None)   
    is_turnaround  = models.BooleanField        (default=False)
    is_terminal    = models.BooleanField        (default=False)
    streak         = models.SmallIntegerField   (null=True, default=None)
    template_employee = models.ForeignKey ("Employee", on_delete=models.CASCADE, null=True, related_name="slot_templates")
    
    html_template = 'sch2/schedule/sch-detail.html'
    
    
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.template().exists():
            self.template_employee = self.template().first().employee
            
    class Meta:
        # ordering = ['shift__start']
        constraints = [
            models.UniqueConstraint(fields=["workday", "shift", "schedule"],    name='Shift Duplicates on day'),
            models.UniqueConstraint(fields=["workday", "employee", "schedule"], name='Employee Duplicates on day'),
        ]
    class Actions:
        def set_template_employee (self, instance, force=True):
            if instance.template().exists():
                if instance.template_employee in instance.siblings_day.values('employee'):
                    if force:
                        slot_to_clear = instance.siblings_day.get(employee=instance.template_employee)
                        slot_to_clear.employee = None
                        slot_to_clear.save()
                    elif force == False:
                        print (
                            "NO ACTION TAKEN", 
                            "EMPLOYEE WORKING NONTEMPLATE SHIFT ON SAME DAY"
                        )  
                else:
                    instance.template_employee = instance.template().first().employee
                    instance.save()
                    print (
                        "TEMPLATING SUCCESSFUL", 
                        f"{instance.employee} TEMPLATED ON {instance.workday.date}"
                        ) 
            else:
                print(
                    "NO ACTION TAKEN",
                    "NO EMPLOYEE IS TEMPLATED FOR THIS SLOT"
                )
        def clear_employee (self, instance):
            if instance.employee != None:
                old_assignment = instance.employee
                instance.employee = None
                instance.save()
                print (f'{old_assignment} cleared from {instance}')
                

                
    actions = Actions()
        
    def template (self):
        return ShiftTemplate.objects.filter(sd_id=self.workday.sd_id,shift=self.shift)
    def slug    (self):
        return self.workday.slug + '-' + self.shift.name
    def start   (self):
        return dt.datetime.combine(self.workday.date, self.shift.start)
    def end     (self):
        return dt.datetime.combine(self.workday.date, self.shift.start) + self.shift.duration
    def hours   (self) :
        return (self.shift.duration.total_seconds() - 1800) / 3600 
    def __str__ (self) :
        return str(self.workday.date.strftime('%y%m%d')) + '-' + str(self.shift) + " " + str(self.employee)
    def streak__display (self):
        return f"#{self.streak} of {self.siblings_streak().count() + 1}"
    def get_absolute_url (self):
        return reverse("slot", kwargs={"slug": self.slug})
    def prefScore         (self) :
        if ShiftPreference.objects.filter(shift=self.shift, employee=self.employee).exists() :
            return ShiftPreference.objects.get(shift=self.shift, employee=self.employee).score
        else:
            return 0
    def _typeATrades (self):
        return self.workday.slots.filter(shift__cls=self.shift.cls,shift__group=self.shift.group).exclude(employee=self.employee).filter(employee__shifts_available=self.shift)
    def isTurnaround (self):
        if self.employee == None:
            return False
        if self.shift.start > dt.time(12,0):
            return False
    def _set_is_turnaround(self) :
        if self.employee == None:
            self.is_turnaround = False
        if self.is_preturnaround() or self.is_postturnaround():
            self.is_turnaround = True
        else:
            self.is_turnaround = False
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
    def is_postturnaround (self) :
        if not self.employee:
            return False
        if self.shift.start > dt.time(18,0):
            return False
        elif self.shift.start > dt.time(13,0) and self.shift.start < dt.time(18,0) :
            if Slot.objects.filter(workday=self.workday.prevWD(), shift__start__gt=dt.time(12,0), employee=self.employee).count() > 0 :
                return True
            else:
                return False
        elif self.shift.start < dt.time(18,0) :
            if Slot.objects.filter(workday=self.workday.nextWD(), shift__start__gt=dt.time(12,0), employee=self.employee).count() > 0 :
                return True
            else:
                return False
    def turnaround_pair   (self) :
        self.save()
        if self.is_turnaround == True:
            return Slot.objects.get(employee=self.employee,workday=self.workday.prevWD())
        if self.is_preturnaround == True:
            return Slot.objects.get(employee=self.employee,workday=self.workday.nextWD())
        else:
            return None
    def is_one_off        (self) :
        if self.employee != None:
            if self.prevSameEmployee() == None and self.nextSameEmployee() == None:
                return True
        return False
    def is_unfavorable  (self):
        if self.employee:
            if self.shift in self.employee.unfavorable_shifts():
                return True
        return False
    def _set_is_terminal  (self) :
        if Slot.objects.filter(workday=self.workday.nextWD(), employee=self.employee).exists() :
            return False
        else:
            return True
    @property   
    def siblings_day     (self) :
        return Slot.objects.filter(workday=self.workday).exclude(shift=self.shift)  
    def siblings_streak (self):
        if self.employee == None:
            return Slot.objects.none()
        siblings = []
        prevDay = self.workday.prevWD()
        while Slot.objects.filter(workday=prevDay, employee=self.employee, schedule=self.schedule).exists() == True:
            siblings += [Slot.objects.get(workday=prevDay, employee=self.employee, schedule=self.schedule).pk]
            prevDay = prevDay.prevWD()
        nextDay = self.workday.nextWD()
        while Slot.objects.filter(workday=nextDay, employee=self.employee).exists() == True:
            siblings += [Slot.objects.get(workday=nextDay, employee=self.employee, schedule=self.schedule).pk]
            nextDay = nextDay.nextWD()
        return Slot.objects.filter(pk__in=siblings).order_by('workday__date')
    def tenable_trades (self):
        primaryScore   = self.prefScore()
        primaryShift   = self.shift
        otherShifts    = self.siblings_day.values('shift')
        otherEmployees = self.siblings_day.values('employee')
        return ShiftPreference.objects.filter(employee=self.employee,shift=self.shift,score__gt=primaryScore)           
    def _streak (self):
        return self.siblings_streak().filter(workday__date__lt=self.workday.date).count() + 1
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
        ------------------------------------------------
        """
        slot = self
        empl_in_conflicting = list(
            slot._get_conflicting_slots().all().values_list(
                'employee',
                flat=True
            ))
        empl_w_ptor  = list(
            PtoRequest.objects.filter(workday=slot.workday.date).values_list(
                    'employee',
                    flat=True
                ).distinct()
            )
        empl_w_tdo   = list(TemplatedDayOff.objects.filter(sd_id=slot.workday.sd_id).values_list(
                    'employee',
                    flat=True
                ).distinct()
            )
        same_day     = list(self.workday.slots.filled().exclude(pk=self.pk).values_list(
                    'employee',
                    flat=True
                ).distinct()
            )
        incompatible = list(set(empl_in_conflicting + empl_w_ptor + empl_w_tdo + same_day))
        if None in incompatible:
            incompatible.remove(None)
        incompatible_employees = Employee.objects.filter(pk__in=incompatible)
        fillable_by = Employee.objects.filter(
            shifts_available=slot.shift).exclude(pk__in=incompatible_employees).distinct()
        return fillable_by
    def fillable_by (self):
        return self._fillableBy()
    def fillWithBestChoice(self):
        self.save()
        choices = self._fillableBy()
        if len(choices) != 0:
            sprefs = ShiftPreference.objects.filter(shift=self.shift, employee__in=choices, score__gte=1).order_by('-score')
        # sort the choices by the best prefScore score
            try:
                if self.template().exists():
                    if self.template().first().employee in choices:
                        self._set_employee( self.template().first().employee )
                        
            except:
                pass
        else:
            if sprefs.exists():
                for x in sprefs:
                    if x in choices:
                        self._set_employee(x.employee)
                        
                    else:
                        pass
        if self.employee == None:
            try :
                self._set_employee(choices [0] )
                try:
                    self.save()
                except:
                    other = self.siblings_day.get(employee=self.employee)
                    if other.template().exists():
                        other.save()
                    else:
                        other.employee = None
                        other.save()
            except:
                pass
        self.save()
    def isFromTemplate (self):
        if self.employee != None:
            if ShiftTemplate.objects.filter(sd_id=self.workday.sd_id,shift=self.shift, employee=self.employee).exists():
                return True
            else:
                return False  
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
        return slots
    def _set_employee (self, employee):
        if ShiftTemplate.objects.filter(sd_id=self.workday.sd_id,employee=employee).exclude(shift=self.shift).exists():
            return 
        if employee in self.siblings_day.values_list('employee',flat=True):
            others = self.siblings_day.filter(employee=employee).update(employee=None)
        self.employee = employee
        self.save()
    def set_sst (self):
        if PtoRequest.objects.filter(workday=self.workday.date, employee=self.employee).exists():
            return "TEMPLATED EMPL HAS ACTIVE PTO REQUEST"
        sst = ShiftTemplate.objects.filter(sd_id=self.workday.sd_id,shift=self.shift)
        if sst.exists():
            if self.employee != None : 
                return "NO SST FILL--- OTHER EMPL OCCUPYING"
            wk_needed_hrs = self.week.needed_hours()[sst.first().employee]
            if wk_needed_hrs < self.shift.hours:
                return "NO SST FILL-- EMPL FTE WOULD BE EXCEEDED"
            if not self.employee:
                if self.workday.slots.filter(employee=sst.first().employee).exists():
                    return "NO SST FILL-- EMPL ALREADY SCHEDULED"
                self.__setattr__('employee', sst.first().employee)
                self.save()
                print (f'Employee set to {sst.first().employee} via Slot@set_sst')
                return "ASSIGNED VIA TEMPLATE"
        return
    def save (self, *args, **kwargs):
        self.streak = self._streak()
        self._save_empl_sentiment ()
        super().save(*args, **kwargs)
    def url (self):
        return reverse('sch:slot-as-streak-view',args=[self.pk])
    def _save_empl_sentiment (self):
        if self.employee == None:
            self.empl_sentiment = None
            return
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
    def shift_sentiment (self):
        if not self.employee:
            return None
        pref = ShiftPreference.objects.filter(employee=self.employee,shift=self.shift)
        if pref.exists():
            return pref.first().score
        else:
            return None
    def createOptionsMap (self):
        empls = Employee.objects.filter(cls=self.shift.cls)
        not_trained = empls.exclude(shifts_trained=self.shift)
        trained = empls.exclude(pk__in=(not_trained.values('pk')))
        not_available = empls.exclude(shifts_available=self.shift)
        available = empls.exclude(pk__in=(not_available.values('pk')))
        
        already_on_day = self.workday.slots.values('employee')
        already_on_day = Employee.objects.filter(pk__in=already_on_day)
        not_on_day = empls.exclude(pk__in=already_on_day.values('pk'))
        
        no_fte_left = []
        for empl in empls:
            pp_hours = sum(list(self.schedule.slots.filter(employee=empl).values_list('shift__hours',flat=True)))
            if self.shift.hours + pp_hours > empl.fte_14_day:
                no_fte_left.append(empl.pk)
        no_fte_left = empls.filter(pk__in=no_fte_left)
        fte_ok = empls.exclude(pk__in=no_fte_left.values('pk'))
        
        no_wk_hrs_left = []
        for empl in empls:
            wk_hours = sum(list(self.week.slots.filter(employee=empl).values_list('shift__hours',flat=True)))
            if self.shift.hours + pp_hours > empl.fte_14_day:
                no_wk_hrs_left.append(empl.pk)
        no_wk_hrs_left = empls.filter(pk__in=no_wk_hrs_left)
        overtime_ok = empls.exclude(pk__in=no_wk_hrs_left.values('pk'))
        
        in_conflicting = self._get_conflicting_slots()
        no_conflicting = empls.exclude(pk__in=in_conflicting.values('pk'))
        
        can = available.intersection(not_on_day,fte_ok,overtime_ok,no_conflicting)

        
        return {'can':can,'sameDay':already_on_day,'notTrained':not_trained,'notAvailable':not_available,'periodOvertime':no_fte_left,'weekOvertime':no_wk_hrs_left,'turnarounds':in_conflicting}
    def prevSameShift (self):
        if self.workday.prevWD():
            if self.workday.prevWD().slots.filter(shift=self.shift).exists() == True: 
                return self.workday.prevWD().slots.get(shift=self.shift)
        return None 
    def nextSameShift (self):
        if self.workday.nextWD():
            if self.workday.nextWD().slots.filter(shift=self.shift).exists() == True: 
                return self.workday.nextWD().slots.get(shift=self.shift)
        return None 
    def prevSameEmployee (self):
        if self.employee != None:
            if self.workday.prevWD():
                if self.workday.prevWD().slots.filter(employee=self.employee).exists() == True: 
                    return self.workday.prevWD().slots.get(employee=self.employee)
        return None 
    def nextSameEmployee (self):
        if self.employee != None:
            if self.workday.nextWD():
                if self.workday.nextWD().slots.filter(employee=self.employee).exists() == True: 
                    return self.workday.nextWD().slots.get(employee=self.employee)
        return None 
    def conflicts (self):
        if self.employee != None:
            cslots = self._get_conflicting_slots().filter(employee=self.employee)
            if cslots.exists():
                return cslots.first()
        return None
    @property
    def pto_conflicts (self):
        return PtoRequest.objects.filter(employee=self.employee, workday=self.workday.date)
    def cssAvailableEmps (self):
        classes = ""
        for empl in self.shift.available.all():
            classes += f"{empl.slug}-available "
        return classes
    def fill_via_swap (self,other):
        
        selfEmployee = self.employee
        otherEmployee = other.employee
        for i in [self, other]:
            i.employee = None
            i.save()
        self.employee = otherEmployee
        other.employee = selfEmployee
        self.save()
        other.save()
        return 
    def predict_consequence (self,employee):
        output = {}
        if employee in self.siblings_day:
            output['conflict'] = 'CONFLICT WITH SAMEDAY'
        sum(list(self.workday.week.slots.filter(employee=employee).values_list('shift__hours',flat=True)))
        
    tags         = TaggableManager()
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
    shift       = models.ForeignKey('Shift', on_delete=models.CASCADE, related_name='shift_templates')
    employee    = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='shift_templates', null=True, blank=True)
    sd_id       = models.IntegerField()


    def __str__(self) :
        return f'{self.shift.name} Template'
    @property
    def url(self):
        return reverse("shifttemplate", kwargs={"pk": self.pk})

    class Meta:
        unique_together = ['shift', 'sd_id']
# ============================================================================
class TemplatedDayOff (models.Model) :
    """
    Fields:
        -  employee
        -  sd_id (0-41) 
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tdos')
    sd_id    = models.IntegerField ()
    
    @property
    def symb (self) :
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZБДЖИЛФШЮЯΔΘΛΞΣΨΩ"[self.sd_id]

    def week (self):
        return self.sd_id // 7
    
    def weekday (self):
        days = "Sun Mon Tue Wed Thu Fri Sat".split(" ")
        return days[self.sd_id % 7]
    
    def __str__ (self) :
        return f'TDO-{self.symb}'
    
    class Meta:
        unique_together = ['employee','sd_id']
# ============================================================================
class PtoRequest (ComputedFieldsModel): 
    employee         = models.ForeignKey (Employee, on_delete=models.CASCADE)
    workday          = models.DateField (null=True, blank=True)
    dateCreated      = models.DateTimeField (auto_now_add=True)
    status           = models.CharField (max_length=20, choices=PTO_STATUS_CHOICES, default='Pending')
    manager_approval = models.BooleanField (default=False)
    sd_id            = models.IntegerField (default=-1)

    @computed (models.BooleanField(), depends=[('self',['status'])])
    def stands_respected (self) -> bool:
        if Slot.objects.filter(workday__date=self.workday, employee=self.employee).count() > 0:
            return False
        return True
    def __str__          (self) :
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
            self.sd_id = Workday.objects.filter(date=self.workday).first().sd_id
        super().save(*args, **kwargs)
    def slot_conflicts (self):
        return Slot.objects.filter(workday__date=self.workday, employee=self.employee)
    def url (self):
        return reverse('sch:pto-request-detail', kwargs={'pk':self.pk})
    
    objects = PtoRequestManager.as_manager()
# ============================================================================
class SlotPriority (models.Model):
    iweekday = models.IntegerField()
    shift    = models.ForeignKey(Shift, on_delete=models.CASCADE)
    priority = models.CharField(max_length=20, choices=PRIORITIES, default='M')

    class Meta:
        unique_together = ['iweekday', 'shift']     
# ============================================================================
class ShiftPreference (ComputedFieldsModel):
    """ SHIFT PREFERENCE [model]
    >>> employee <fkey> 
    >>> shift    <fkey>
    >>> priority <str> SP/P/N/D/SD
    >>> score    <int> -2/-1/0/1/2
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shift_prefs')
    shift    = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='shift_prefs')
    priority = models.CharField(max_length=2, choices=PREF_SCORES, default='N')

    @computed (models.IntegerField(), depends=[('self',['priority'])])
    def score (self):
        scoremap = { 'SP':2, 'P':1, 'N':0, 'D':-1, 'SD':-2 }
        return scoremap[self.priority]

    class Meta:
        unique_together = ['employee', 'shift']
    def save (self,*args,**kwargs):
        super().save(*args,**kwargs)
        for slot in Slot.objects.filter(employee=self.employee,shift=self.shift):
            slot.save()
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
# ============================================================================
class ShiftSortPreference (models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shift_sort_prefs')
    shift    = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="shift_sort_prefs")
    score    = models.IntegerField(default=0)
    rank     = models.IntegerField(default=1)
    class Meta: 
        unique_together = ['employee', 'shift']
        ordering        = ['score',    'shift']
    def __str__(self):
        return f"[{self.shift} SortPref]"
    def save(self,**kwargs):
        self.rank = self.score + 1
        super().save(**kwargs)
# ============================================================================
def generate_schedule (year,number):
    """
    GENERATE SCHEDULE
    =================
    args: 
        - year
        - number
    """
    yeardates = []
    for date in SCH_STARTDATE_SET:
        if date.year == year:
            yeardates.append(date)
    yeardates.sort()
    n = Schedule.objects.filter(year=year,number=number).count()
    start_date = yeardates[number - 1]
    
    n_same = 0
    if Schedule.objects.filter(year=year, number=number).exists(): 
        n_same = Schedule.objects.filter(year=year, number=number).count()
    version = "ABCDEFGHIJKLMNOP"[n_same]

    Schedule.objects.create(start_date=start_date, number=number, year=year, version=version)
    
def randomSlot ():
    import random 
    
    slotn = random.randint (0,Slot.objects.count())
    slot  = Slot.objects.all()[slotn]
    
    return slot

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

def sortDict (d, reverse=False):
    """ SORT DICT BY VALUE """
    if reverse == True:
        return dict(sorted(d.items(), key=lambda item: item[1], reverse=True))
    return {k: v for k, v in sorted(d.items(), key=lambda item: item[1])}

def dayLetter (i):
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZБДЖИЛФШЮЯΔΘΛΞΣΨΩ"

def analyzeTrade (pkA, pkB):
    """ Analyze if a slot trade is tenable """
    slotA = Slot.objects.get(pk=pkA)
    slotB = Slot.objects.get(pk=pkB)
    employees   = Employee.objects.filter(pk__in=[slotA.employee.pk, slotB.employee.pk])
    shifts      = Shift.objects.filter(pk__in=[slotA.shift.pk, slotB.shift.pk])
    workdays    = Workday.objects.filter(pk__in=[slotA.workday.pk, slotB.workday.pk])
    
    if slotA.employee == slotB.employee:
        return False
    
