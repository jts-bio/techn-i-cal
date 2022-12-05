from django.db import models
from autoslug import AutoSlugField

# Create your models here.
class Shift (models.Model):
    slug = AutoSlugField(populate_from=['name','cls'], primary_key=True )
    cls = models.CharField(max_length=5)
    name = models.CharField(max_length=50)
    start = models.TimeField()
    block = models.IntegerField()
    
    class Meta:
        ordering = ['cls','start','name']
        unique_together = ['name', 'cls']
         
    
class Workday (models.Model):
    slug = AutoSlugField(populate_from=['date'], primary_key=True)
    date = models.DateField()
    start = models.TimeField()
    finish = models.TimeField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="workdays")
    
    class Meta:
        unique_together = [
            ('date', 'shift')
        ]

class AbstractSlot (models.Model):
    sch_day = models.IntegerField()
    hours   = models.IntegerField()
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE, related_name="slots")

    class Meta:
        abstract = True
        unique_together = [
            ('sch_day', 'employee')
        ]
    

class Slot (AbstractSlot):
    slug = AutoSlugField(populate_from=['workday','shift', 'employee'], primary_key=True)
    workday = models.ForeignKey(Workday, on_delete=models.CASCADE, related_name="slots")
    shift  = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="slots")
    

    

    
    


class Employee (models.Model):
    name = models.CharField(max_length=128)
