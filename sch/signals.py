from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Slot, Schedule, ShiftTemplate, TemplatedDayOff, PtoRequest, Employee, Shift, Workday, Week, Period



@receiver(post_save, sender=Slot)
def update_schedule_percent_complete(sender, instance, **kwargs):
    print("Updating schedule percent complete")
    schedule = instance.schedule
    schedule.update_percent()
    schedule.save()
    
    
@receiver(post_save, sender=Slot)
def update_other_slots(sender, instance, **kwargs):
    print("Updating other slots")
    workday = instance.workday
    workday.slots.filter(employee=instance.employee).exclude(pk=instance.pk).update(employee=None)
    