import datetime as dt
from re import sub

from computedfields.models import ComputedFieldsModel, computed
from django.db import models
from django.db.models import (Avg, Count, DurationField, ExpressionWrapper, F,
                              FloatField, Max, Min, OuterRef, Q, QuerySet,
                              StdDev, Subquery, Sum, Variance )
from django.urls import reverse
from multiselectfield import MultiSelectField

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

DAYCHOICES    = (
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
TODAY         = dt.date.today()


#* --- --- Managers --- --- *#
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
# ============================================================================
class EmployeeManager (models.QuerySet):

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
    def weekly_hours(self, year, week):
        return Employee.objects.annotate(
                hours=Subquery(Slot.objects.filter(workday__date__year=year,workday__iweek=week, employee=F('pk')).aggregate(hours=Sum('hours')))
            )
    def can_fill_shift_on_day (self, shift, workday, method="available"):
        week = workday.iweek
        year = workday.date.year
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

#* === === MODELS === === *#
# ============================================================================
class Shift (ComputedFieldsModel) :
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
    name            = models.CharField(max_length=100)
    fte_14_day      = models.FloatField()
    shifts_trained  = models.ManyToManyField(Shift, related_name='trained')
    shifts_available= models.ManyToManyField(Shift, related_name='available')
    streak_pref     = models.IntegerField(default=3)
    trade_one_offs  = models.BooleanField(default=True)
    cls             = models.CharField(choices=(('CPhT','CPhT'),('RPh','RPh')),default='CPhT',blank=True, null=True,max_length=4)
    evening_pref    = models.BooleanField(default=False)
    

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
        
    
    def ftePercForWeek (self, year, iweek):
        if self.fte == 0:
            return 0.8
        if self.weekly_hours(year,iweek) == None:
            return 0
        return  self.weekly_hours(year,iweek) / (Employee.objects.get(pk=self.pk).fte_14_day/ 2)
    
    def count_shift_occurances (self):
        slots = Slot.objects.filter(employee=self).values('shift__name')
        return slots.distinct().annotate(count=Count('shift__name'))
    
    @property
    def get_TdoSlotConflicts (self):
        tdos = list(TemplatedDayOff.objects.filter(employee=self).values_list('pk',flat=True))
        return Slot.objects.filter(workday__sd_id__in=tdos, employee=self)

    def info_printWeek(self,year,week):
            slots = list(Slot.objects.filter(employee=self,workday__date__year=year,workday__iweek=week).values_list('shift__name',flat=True))
            return f'{self.name}: {slots}'
    
       
    objects = EmployeeManager.as_manager()
# ============================================================================
class Workday (ComputedFieldsModel) :
    # fields: date, shifts 
    date = models.DateField()
    week = models.ForeignKey("week", on_delete=models.CASCADE, null=True, related_name='workdays')

    __all__ = ['date','slug','iweekday','iweek','iperiod','ppd_id','weekday',
               'shifts',
               'filledSlots','n_slots',"n_emptySlots",'n_shifts','percFilled',
               'siblings_iweek']


    @computed(models.SlugField(max_length=20), depends=[('self',['date'])])
    def slug (self) -> str: 
        return self.date.strftime('%Y-%m-%d')

    @computed(models.IntegerField(null=True), depends=[('self',['date'])])
    def iweekday (self) -> int:
        # range 0 -> 6
        return int (self.date.strftime('%w'))
    
    @computed(models.IntegerField(null=True), depends=[('self',['date'])])
    def iweek (self) -> int:
        # range 0 -> 53
        return int (self.date.strftime('%U'))
    
    # @computed(models.CharField(max_length=20,blank=True), depends=[('self',['date'])])
    # def weekId (self) :
    #     w = int(self.date.strftime('%U'))
    #     year = self.date.year -1 if w is 0 else self.date.year 
    #     return f'{year}-W{w}'
    
    @computed(models.IntegerField(), depends=[('self',['date'])])
    def iperiod (self) -> int:
        # range 0 -> 27
        return int (self.date.strftime('%U')) // 2
    
    # @computed(models.CharField(max_length=20,blank=True), depends=[('self',['date'])])
    # def periodId (self):
    #     p = int(self.date.strftime('%U')) // 2
    #     year = self.date.year -1 if p is 0 else self.date.year 
    #     return f'{year}-P{p}'

    @computed(models.IntegerField(), depends=[('self',['date'])])
    def ppd_id (self) -> int:
        # range 0 -> 13
        return (self.date - dt.date(2022,9,4)).days % 14
    
    @computed(models.CharField(max_length=20,null=True), depends=[('self',['iperiod'])])
    def ischedule (self) -> int:
        # range 0 -> 9
        if self.iperiod:
            return self.iperiod // 3 
        else:
            return 

    @computed(models.IntegerField(),depends=[('self',['date'])])
    def sd_id (self) -> int:
        # range 0 -> 41
        return (self.date - dt.date(2022,9,4)).days % 42
    
    # @computed(models.CharField(max_length=20,blank=True), depends=[('self',['date'])])
    # def scheduleId (self):
    #     s = int(self.date.strftime('%U')) // 6
    #     year = self.date.year -1 if s is 0 else self.date.year 
    #     return f'{year}-S{s}'
    
    @property
    def weekday (self) -> str :
        # Sun -> Sat
        return self.date.strftime('%a')
    
    @property
    def shifts (self) -> ShiftManager:
        return Shift.objects.filter(occur_days__contains= self.iweekday) 
    
    @property
    def filledSlots (self) -> SlotManager:
        return Slot.objects.filter(workday=self)
    
    @property
    def n_slots (self) -> SlotManager:
        return Slot.objects.filter(workday=self).count()
    
    @property
    def emptySlots (self) -> ShiftManager:
        filled = self.filledSlots.values('shift')
        return Shift.objects.filter(occur_days__contains= self.iweekday).exclude(pk__in=filled)

    @property
    def n_shifts (self) -> ShiftManager:
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
    def iweek_of (self) -> "WorkdayManager":
        return self.siblings_iweek.first()

    @property
    def siblings_iperiod (self) -> "WorkdayManager":
        return Workday.objects.filter(date__year=self.date.year, iperiod=self.iperiod)

    @property
    def iperiod_of (self) -> "WorkdayManager":
        return self.siblings_iperiod.first()

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
    def days_away (self) -> int:
        td = self.date - TODAY 
        return td.days

    def related_slots (self) -> "SlotManager":
        return Slot.objects.filter(workday=self)

    @property
    def n_unfilled (self) -> int:
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
                    pk__in=current.pk)
        return Employee.objects.can_fill_shift_on_day(workday=self,shift=shift)
    
    def n_can_fill (self, shift):
        if self.who_can_fill == None:
            return None 
        return self.who_can_fill(shift).count()
        
    
    objects = WorkdayManager.as_manager()
# ============================================================================  
class Week (ComputedFieldsModel) :
    __all__ = [
        'year','iweek','prevWeek','nextWeek',
    ]
    
    iweek = models.IntegerField() 
    year  = models.IntegerField()

    @property
    def slug (self) -> str: 
        return f'{self.year}_{self.iweek}'

    @property
    def name (self) -> str: 
        return f'{self.year}_{self.iweek}'
    
    def prevWeek (self) -> "Week":
        try:
            return Week.objects.get(year=self.year, iweek=self.iweek-1)
        except Week.DoesNotExist:
            # go back 1 year, and get the max iweek of that year.
            yearnew = self.year - 1
            iweeknew = Week.objects.filter(year=yearnew).aggregate(Max('iweek'))['iweek__max']
            return Week.objects.get(year=yearnew, iweek=iweeknew)
        
    def nextWeek (self) -> "Week":
        try:
            return Week.objects.get(year=self.year, iweek=self.iweek+1)
        except Week.DoesNotExist:
            # go forward 1 year, and get the 0 iweek of that year.
            yearnew = self.year + 1
            try:
                return Week.objects.get(year=yearnew, iweek=0)
            except:
                return Week.objects.get(year=yearnew, iweek=1)
    
         
    def workdays (self):
        return Workday.objects.filter(date__year=self.year,iweek=self.iweek)
    
    
    def slots (self):
        return Slot.objects.filter(workday__in=self.workdays)
    
    
    def __str__ (self) :
        return f'{str(self.year)[2:]}-W{str(self.iweek)}'
# ============================================================================
class Slot (ComputedFieldsModel) :
    # fields: workday, shift, employee
    workday  = models.ForeignKey("Workday",  on_delete=models.CASCADE)
    shift    = models.ForeignKey( Shift,     on_delete=models.CASCADE)
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE, null=True, blank=True)
    empl_sentiment = models.SmallIntegerField (default=50)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workday", "shift"], name='Shift Duplicates on day'),
            models.UniqueConstraint(fields=["workday", "employee"], name='Employee Duplicates on day')
            ]
        
    # computed fields:
    @computed(models.SlugField(max_length=20), depends=[('self',['workday','shift'])])
    def slug (self):
        return self.workday.slug + '-' + self.shift.name
    def start (self):
        return dt.datetime.combine(self.workday.date, self.shift.start)
    def end (self):
        return dt.datetime.combine(self.workday.date, self.shift.start) + self.shift.duration
    @computed(models.FloatField(), depends=[('self',['shift'])])
    def hours (self) -> float:
        return (self.shift.duration.total_seconds() - 1800) / 3600 
    def __str__(self) :
        return str(self.workday.date.strftime('%y%m%d')) + '-' + str(self.shift) + " " + str(self.employee)
    def get_absolute_url(self):
        return reverse("slot", kwargs={"slug": self.slug})
    @property
    def prefScore (self) -> int:
        if ShiftPreference.objects.filter(shift=self.shift, employee=self.employee).exists() :
            return ShiftPreference.objects.get(shift=self.shift, employee=self.employee).score
        else:
            return 0
    @computed (models.IntegerField(), depends=[('self',['workday'])])
    def is_turnaround (self) -> bool:
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
    def is_preturnaround (self) -> bool:
        if not self.employee:
            return False
        if self.shift.start < dt.time(12,0):
            return False
        elif self.shift.start > dt.time(12,0) :
            if Slot.objects.filter(workday=self.workday.nextWD(), shift__start__lt=dt.time(12,0), employee=self.employee).count() > 0 :
                return True
            else:
                return False
    def turnaround_pair (self) -> 'Slot':
        self.save()
        if self.is_turnaround :
            return Slot.objects.get(employee=self.employee,workday=self.workday.prevWD())
        if self.is_preturnaround :
            return Slot.objects.get(employee=self.employee,workday=self.workday.nextWD())
        else:
            return None
    @computed (models.BooleanField(), depends=[('self',['workday'])])
    def is_terminal (self):
        if Slot.objects.filter(workday=self.workday.nextWD(), employee=self.employee).exists() :
            return False
        else:
            return True
    @property   
    def siblings_day (self) -> SlotManager:
        return Slot.objects.filter(workday=self.workday).exclude(shift=self.shift)
    
    @property
    def tenable_trades (self):
        primaryScore = self.prefScore
        primaryShift = self.shift
        otherShifts = self.siblings_day.values('shift')
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
    def isOverStreakPref (self) -> bool :
        if not self.employee:
            return False
        if self.streak:
            return self.streak > self.employee.streak_pref
        else:
            return False
        
    @property 
    def shouldBeTdo (self) -> bool:
        """EMPLOYEE SHOULD NOT WORK THIS DAY BECAUSE OF A TEMPLATED DAY OFF OBJECT"""
        if TemplatedDayOff.objects.filter(employee=self.employee, sd_id=self.workday.sd_id).exists():
            return True
        else:
            return False
    
    def fillableBy (self):
        trained = Employee.objects.filter(shifts_trained=self.shift)
        otherShiftToday = self.siblings_day.values('employee')
        can_fill = trained.exclude(pk__in=otherShiftToday)
        if self.shift.start > dt.time(10):
            conflictingSlots = Slot.objects.filter(workday=self.workday.nextWD(),shift__start__hour__lt=10).values('employee')
            can_fill = can_fill.exclude(pk__in=conflictingSlots)
        if self.shift.start < dt.time(10):
            conflictingSlots = Slot.objects.filter(workday=self.workday.prevWD(),shift__start__hour__gt=10).values('employee')
            can_fill = can_fill.exclude(pk__in=conflictingSlots)
        if self.shift.start == dt.time(10):
            conflictingAfter  = Slot.objects.filter(workday=self.workday.nextWD(),shift__start__hour__lt=10).values('employee')
            conflictingBefore = Slot.objects.filter(workday=self.workday.prevWD(),shift__start__hour__gt=10).values('employee')
            can_fill = can_fill.exclude(pk__in=conflictingAfter).exclude(pk__in=conflictingBefore)
        
        return can_fill 
    
    def isFromTemplate (self) -> bool:
        if self.employee:
            if ShiftTemplate.objects.filter(ppd_id=self.workday.sd_id, employee=self.employee).exists():
                return True
            else:
                return False
    
    def conflicting_slots (self) -> SlotManager:
        if self.shift.start.hour > 10:
            slots = Slot.objects.filter(workday=self.workday.nextWD(), shift__start__hour__lt=10)
        elif self.shift.start.hour < 10:
            slots = Slot.objects.filter(workday=self.workday.prevWD(), shift__start__hour__gt=10)
        elif self.shift.start.hour == 10:
            slots = Slot.objects.filter(workday=self.workday.nextWD(), shift__start__hour__lt=10) | Slot.objects.filter(workday=self.workday.prevWD(), shift__start__hour__gt=10)
        return slots
    
    objects = SlotManager.as_manager()
# ============================================================================
class ShiftTemplate (models.Model) :
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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    ppd_id   = models.IntegerField(null=True) 
    sd_id    = models.IntegerField()
    
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
PTO_STATUS_CHOICES = (
    ('P', 'Pending'),
    ('A', 'Approved'),
    ('D', 'Denied'),
)
class PtoRequest (ComputedFieldsModel): 
    employee         = models.ForeignKey(Employee, on_delete=models.CASCADE)
    workday          = models.DateField(null=True, blank=True)
    dateCreated      = models.DateTimeField(auto_now_add=True)
    status           = models.CharField(max_length=20, choices=PTO_STATUS_CHOICES, default='P')
    manager_approval = models.BooleanField(default=False)
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

PRIORITIES = (
    ('L', 'Low'),
    ('M', 'Medium'),
    ('H', 'High'),
    ('U', 'Urgent'),
)
class SlotPriority (models.Model):
    iweekday = models.IntegerField()
    shift    = models.ForeignKey(Shift, on_delete=models.CASCADE)
    priority = models.CharField(max_length=20, choices=PRIORITIES, default='M')

    class Meta:
        unique_together = ['iweekday', 'shift']     
# ============================================================================

PREF_SCORES = (
    ('SP', 'Strongly Prefer'),
    ('P', 'Prefer'),
    ('N', 'Neutral'),
    ('D', 'Dislike'),
    ('SD', 'Strongly Dislike'),
)
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


