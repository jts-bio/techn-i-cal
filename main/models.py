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
                              Variance)
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.urls import reverse
from django_group_by import GroupByMixin
from taggit.managers import TaggableManager
from multiselectfield import MultiSelectField
from .fields import slugify
        
    

class Organization (models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField ()
    
    __str__ = lambda self: f"{self.name}"
    
class Department (models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField ()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments', null=True, blank=True)
    schedule_week_count = models.IntegerField(default=6)
    schedule_period_count = models.IntegerField(default=3)
    schedule_start_date = models.DateField(default=dt.date(2022, 12, 25))
    
    __str__ = lambda self: f"{self.name}"
    
    
class Shift (models.Model):
    WEEKDAY_CHOICES = (("S", "Sunday"),("M", "Monday"),("T", "Tuesday"),("W", "Wednesday"),("R", "Thursday"),("F", "Friday"),("A", "Saturday"))
    
    name = models.CharField(max_length=300)
    slug = models.SlugField ()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='shifts', null=True, blank=True)
    weekdays = MultiSelectField(max_length=100, choices=WEEKDAY_CHOICES, default="S M T W R F A".split(" "))
    hours = models.SmallIntegerField()
    
    __str__ = lambda self: f"{self.name}"
    
   
    
class Employee (models.Model):
    name = models.CharField(max_length=300)
    initials = models.CharField(max_length=4,unique=True)
    slug = models.SlugField ()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees', null=True, blank=True)
    hire_date = models.DateField(default=dt.date(2020, 5, 1))
    active = models.BooleanField()
    
    __str__ = lambda self: f"{self.name}"

        
class Schedule (models.Model):
    start_date = models.DateField()
    year = models.SmallIntegerField()
    number = models.SmallIntegerField()
    slug = models.SlugField()
    published = models.BooleanField(default=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
    published_version = models.OneToOneField('Version', on_delete=models.SET_NULL, null=True, blank=True, related_name='published_version')
    
    __str__ = lambda self: f"{self.year}:{self.number}"
    
class Version (models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='versions')
    name = models.CharField(max_length=1)
    percent = models.SmallIntegerField()
    
    __str__ = lambda self: f"{self.schedule.year}{self.schedule.number}:{self.name}"
    
    
    
    
    
    
    