import datetime as dt
import json
import random
import statistics
from re import sub

import yaml
from django.contrib.auth.models import User
from django.db import models
from django.db.models import (Avg, Count, Deferrable, DurationField,
                              ExpressionWrapper, F, FloatField, Max, Min,
                              OuterRef, Q, QuerySet, StdDev, Subquery, Sum,
                              Variance, Value, When, Window, fields)

from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.urls import reverse
from django_group_by import GroupByMixin
from taggit.managers import TaggableManager
from multiselectfield import MultiSelectField
from django.utils import timezone
from .fields import slugify
from django.contrib.auth.models import User
from django.dispatch import receiver, Signal


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        'Organization', on_delete=models.CASCADE, related_name='profiles', null=True, blank=True)
    admin = models.BooleanField(default=False)

    def __str__(self): return f"{self.user.username}"


class Organization (models.Model):

    name = models.CharField(max_length=300)
    slug = models.SlugField()

    def __str__(self): return f"{self.name}"

    @property
    def employees(self): return Employee.objects.filter(department__organization=self)


class Department (models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField()
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='departments', null=True, blank=True)
    schedule_week_count = models.IntegerField(
        choices=[(2, 2), (4, 4), (6, 6), (8, 8)], default=6)
    schedule_start_date_init = models.DateField(default=dt.date(2022, 12, 25))

    @property
    def schedule_start_dates(self): return [
        self.schedule_start_date_init + dt.timedelta(days=7*self.schedule_week_count*i) for i in range(20)]
    
    def unused_schedule_start_dates(self): return [
        d for d in self.schedule_start_dates if not Schedule.objects.filter(department=self, start_date=d).exists()]

    class Meta:
        unique_together = ('name', 'organization')
        #

    def __str__(self): return f"{self.name} [{self.organization.name}]"


class Shift (models.Model):
    WEEKDAY_CHOICES = (("S", "Sunday"), ("M", "Monday"), ("T", "Tuesday"),
                       ("W", "Wednesday"), ("R", "Thursday"), ("F", "Friday"), ("A", "Saturday"))
    PHASE_CHOICES = ((0, "AM"), (1, "MD"), (2, "PM"), (3, "EV"), (4, "XN"))

    name = models.CharField(max_length=300)
    slug = models.SlugField(primary_key=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='shifts', null=True, blank=True)
    weekdays = MultiSelectField(
        max_length=100, choices=WEEKDAY_CHOICES, default="S M T W R F A".split(" "))
    hours = models.SmallIntegerField(default=10)
    phase = models.IntegerField(choices=PHASE_CHOICES, default=0)
    on_holidays = models.BooleanField(default=True)

    def __str__(self): return f"{self.name}"


class Employee (models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField(primary_key=True)
    initials = models.CharField(max_length=4)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='employees', null=True, blank=True)
    fte = models.FloatField(default=1.0)
    hire_date = models.DateField(default=dt.date(2020, 5, 1))
    active = models.BooleanField(default=True)
    std_weekly_hours = models.SmallIntegerField(default=40)

    shifts_trained = models.ManyToManyField(Shift, related_name='employees_trained', blank=True,
                                            help_text="All shifts this employee is trained to work.")

    shifts_available = models.ManyToManyField(Shift, related_name='employees_available', blank=True,
                help_text="""All shifts this employee is available to work and is in the active rotation for. 
                            Trained shifts not also marked as available will never be scheduled by the AI, 
                            but will allow for manual assignments.""")

    def __str__(self): return f"{self.name}"

    @property
    def url(self): return reverse('emp-shift-pref', args=[self.pk])


class Schedule (models.Model):

    start_date = models.DateField()
    year = models.SmallIntegerField()
    number = models.SmallIntegerField()
    slug = models.SlugField()
    published = models.BooleanField(default=False)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
    employees = models.ManyToManyField(Employee, related_name='schedules', blank=True)

    def __str__(self): return f"{self.year}:{self.number}"

    @property
    def url(self): return reverse('sch-detail', args=[self.department.slug, self.year, self.number])

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['year', 'number', 'department'], name='schedule')
        ]


class Version (models.Model):
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name='versions')
    name = models.CharField(max_length=1)
    percent = models.SmallIntegerField()
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='versions_created', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=3, default="DFT", 
                              choices=(("DFT", "Draft"), ("PUB", "Published"), ("ARC", "Archived")), null=True, blank=True)

    def __str__(
        self): return f"{self.schedule.year}:{self.schedule.number}.{self.name}"
    
    @property
    def created_ago(self): return (timezone.now() - self.created_at).days

    @property
    def url(self): return reverse('ver-detail', 
                args=[self.schedule.department.slug, self.schedule.year, self.schedule.number, self.name])

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'name'], name='version')
        ]

    def slot_count(self): return Slot.objects.filter(workday__version=self).count()


class PtoRequest (models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='pto_requests')
    schedule = models.ForeignKey(
        'ScheduleBasePtoCalendar', on_delete=models.CASCADE, related_name='pto_requests', null=True, blank=True)
    sdid = models.SmallIntegerField(default=0)

    def __str__(self): return f"{self.employee}:{self.start_date}"


class DayOffMap (models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='day_off_maps')
    days_off = models.CharField(max_length=100, default="",help_text="Comma-separated list of days off, e.g. 'M,T,W'")

    def __str__(self): return f"{self.employee} TDO-Map"


class Workday (models.Model):

    date = models.DateField()
    version = models.ForeignKey(
        Version, on_delete=models.CASCADE, related_name='workdays')
    sdid = models.SmallIntegerField(default=0)
    wkid = models.SmallIntegerField(default=0)
    pdid = models.SmallIntegerField(default=0)
    
    @property
    def weekday(self): return self.date.strftime("%A")

    def __str__(self): return f"{self.date}"

    def previous(self): 
        if self.sdid == 1:  return None
        else:               return Workday.objects.get(version=self.version,sdid=self.sdid-1)

    def next(self): 
        if self.sdid == 42: return None
        else:               return Workday.objects.get(version=self.version,sdid=self.sdid+1)


class ScheduleBasePtoCalendar (models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='pto_calendars')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pto_calendars')

    def __str__(self): return f"{self.employee} PTO-Calendar"


class Slot (models.Model):
    slug = models.SlugField()
    workday = models.ForeignKey(
        Workday, on_delete=models.CASCADE, related_name='slots')
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, related_name='slots')
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)

    def __str__(self): return f"{self.workday.date}:{self.shift.name}"

    @property
    def url (self): return reverse('slt-detail', 
                                   args=[self.workday.version.schedule.department.slug, 
                                         self.workday.version.schedule.year, 
                                         self.workday.version.schedule.number, 
                                         self.workday.version.name, 
                                         self.workday.date, 
                                         self.shift.slug])

    def conflicting_slots(self): 
        if self.shift.phase < 2:
            if self.workday.sdid != 1:
                return self.workday.previous().slots.filter(shift__phase__gt=self.shift.phase)
        elif self.shift.phase >= 2:
            if self.workday.sdid != 42:
                return self.workday.next().slots.filter(shift__phase__lt=self.shift.phase)
        return Slot.objects.none()
    
    def get_conflicting(self):
        if self.conflicting_slots():
            return set(self.conflicting_slots().values_list('employee__pk', flat=True)).difference({None})
        else:
            return Employee.objects.none()

    def fills_with(self):
        others_on_wd = list(set(self.workday.slots.exclude(pk=self.pk).values_list('employee__pk', flat=True)).difference({None}))
        in_conflict_slot = list(self.get_conflicting())
        if in_conflict_slot:
            excluding = Employee.objects.filter(pk__in=others_on_wd+in_conflict_slot)
        else:
            excluding = Employee.objects.none()
        dept = self.workday.version.schedule.department
        ver = self.workday.version
        schver = self.workday.version
        empls = self.workday.version.schedule.employees.all()
        wkid = self.workday.wkid
        pdid = self.workday.pdid

        weekhours = Slot.objects.filter(
            workday__version=ver, 
            workday__wkid=wkid, 
            employee=OuterRef('pk')
        ).values('employee').annotate(
            weekhours=Sum('shift__hours')
        ).values('weekhours')[:1]
        
        pdhours = Slot.objects.filter(
            workday__version=ver,
            workday__pdid=pdid,
            employee=OuterRef('pk')
        ).values('employee').annotate(
            pdhours=Sum('shift__hours')
        ).values('pdhours')[:1]

                
        return self.shift.employees_available.exclude(pk__in=excluding).annotate(
            weekhours=Coalesce(weekhours,0),
            pdhours=Coalesce(pdhours,0),
        ).filter(weekhours__lt=F('std_weekly_hours')).order_by('-weekhours', 'pdhours')
    

class ShiftPref (models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shift_prefs')
    shift    = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='shift_prefs')
    rank     = models.SmallIntegerField(default=0)
    qual     = models.SmallIntegerField(default=0, choices=((0,"SD"),(1,"D"),(2,"N"),(3,"P"),(4,"SP")))     


class PtoSlot (Slot):
    shift = None


class EmployeeScheduleTemplateMap (models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedule_templates')
    active_date = models.DateField(default=dt.date(2020, 5, 1))

    def __str__(self): return f"{self.employee} Schedule Template"

class EmployeeTemplateSlot (models.Model):
    template_map = models.ForeignKey(EmployeeScheduleTemplateMap, on_delete=models.CASCADE, related_name='slots')
    kind = models.CharField(max_length=3, choices=(("SFT","Shift"),("PTO","PTO"),("TDO","TDO"),("GEN","Generic")))
    sdid = models.SmallIntegerField(default=0)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='template_slots', null=True, blank=True)
    phase = models.SmallIntegerField(default=0, choices=((0,"AM"),(1,"MD"),(2,"PM"),(3,"EV"),(4,"XN")))

    def __str__(self): return f"{self.template_map.employee} Template Slot"


