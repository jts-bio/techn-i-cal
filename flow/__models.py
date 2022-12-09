from django.db import models
from autoslug import AutoSlugField


CLASSES = (('CPhT','CPhT'),('RPh','RPh'))
TIMEBLOCKS = (('AM','AM'),('MD','MD'),('PM','PM'),('PM2','PM2'),('ON','ON'))
# Create your models here.
class Shift (models.Model):
    slug = AutoSlugField(populate_from=['name','cls'], primary_key=True )
    cls = models.CharField(choices=CLASSES, max_length=5)
    name = models.CharField(max_length=50)
    start = models.TimeField()
    block = models.CharField(choices=TIMEBLOCKS, max_length=5)
    
    class Meta:
        ordering = ['cls','start','name']
        unique_together = ['name', 'cls']
         
class Workday (models.Model):
    slug = AutoSlugField(populate_from=['date'], primary_key=True)
    date = models.DateField()
    week = models.ForeignKey("Week", on_delete=models.CASCADE, related_name="workdays")
    period = models.ForeignKey("Period", on_delete=models.CASCADE, related_name="workdays")
    schedule = models.ForeignKey("Schedule", on_delete=models.CASCADE, related_name="workdays")
    
    class Meta:
        unique_together = [
            ('date', 'schedule')
        ]
  
class Employee (models.Model):
    name = models.CharField(max_length=128)
    initials = models.CharField(max_length=5)
    fte = models.FloatField()
    shifts_trained = models.ManyToManyField(Shift, related_name="employees")
    
    class Actions:
        def add_pto_request(self, date):
            if Slot.objects.filter(employee=self, workday__date=date).exists():
                raise Exception("Employee not available on date {}".format(date))
            PtoRequest.objects.create(employee=self, date=date)
    
class Slot (models.Model):
    slug = AutoSlugField(populate_from=['workday','shift', 'employee'], primary_key=True)
    workday = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name="slots")
    shift  = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="slots")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="employee")
    sentiment = models.IntegerField(null=True, blank=True, default=None)

class Week (models.Model):
    slug = AutoSlugField(populate_from=['year','week'], primary_key=True)
    number = models.IntegerField()
    period = models.ForeignKey("Period", on_delete=models.CASCADE, related_name="weeks")
    schedule = models.ForeignKey("Schedule", on_delete=models.CASCADE, related_name="weeks")
    
class Schedule (models.Model):
    slug = AutoSlugField(populate_from=['year','schedule','version'], primary_key=True)
    version = models.CharField(max_length=2)
    schedule = models.IntegerField()
    year = models.IntegerField()

class Period (models.Model):
    slug = AutoSlugField(populate_from=['schedule','period'], primary_key=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="periods")

class PtoRequest (models.Model):
    slug = AutoSlugField(populate_from=['date','employee'],primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="pto_requests")
    date = models.DateField()
    
    
    
    