from django.db import models
import datetime as dt
# Create your models here.

class Shift (models.Model):
    name = models.CharField(max_length=5)
    start = models.TimeField()
    hours = models.IntegerField()
    # Auto-calculated
    duration = models.DurationField(default=dt.timedelta(hours=0))
    
    
    def _set_duration(self):
            if self.hours >= 5:
                brk = dt.timedelta(minutes=30)
            else:
                brk = dt.timedelta(minutes=0)
            self.__setattr__('duration', dt.timedelta(hours=self.hours) + brk)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_duration()