from django.db.models.signals import post_save, post_delete, pre_save, pre_delete, post_init
from django.dispatch import receiver
from ..sch.models import Slot, Schedule, ShiftTemplate, TemplatedDayOff, PtoRequest, Employee, Shift, Workday, Week, Period


# SCHEDULE SIGNALS
@receiver(post_save, sender=Slot)
def update_schedule_percent_complete(sender, instance, **kwargs):
    print("Updating schedule percent complete")
    schedule = instance.schedule
    schedule.update_percent()
    schedule.save()

# SLOT SIGNALS 
@receiver(post_save, sender=Slot)
def update_other_slots(sender, instance, **kwargs):
    print("Updating other slots")
    workday = instance.workday
    workday.slots.filter(employee=instance.employee).exclude(pk=instance.pk).update(employee=None)

@receiver(post_init, sender=Slot)
def calc_slot_hours(sender, instance, **kwargs):
    if instance.hours == None:
        instance.hours = instance._set_hours()
    
