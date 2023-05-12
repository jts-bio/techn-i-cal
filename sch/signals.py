from .models import *
from django.db.models.signals import post_save, pre_save, m2m_changed, post_init
from django.dispatch import receiver, Signal
from django.db.models import Sum

from .subsignals.turnaround_signals import (
   create_turnaround, 
   delete_turnaround
)

from .subsignals.week_signals import (
   assign_version 
)


@receiver(post_save, sender=Slot)
def clear_fills_with_on_conflicting_slot(sender, instance, **kwargs):
   if instance.employee != None:
      for slot in instance._get_conflicting_slots():
         slot.fills_with.remove(instance.employee)
          

@receiver(post_save, sender=Slot)
def remove_employee_from_same_workday_fills(sender, instance, **kwargs):
   if instance.employee != None:
      for slot in instance.workday.slots.exclude(pk=instance.pk).filter(fills_with=instance.employee):
         slot.fills_with.remove(instance.employee)

@receiver(pre_save, sender=Slot)
def remove_employee_from_assignments_on_same_workday(sender, instance, **kwargs):
   if instance.employee != None:
      for assignment in instance.workday.slots.filter(employee=instance.employee).exclude(pk=instance.pk):
         assignment.employee = None
         
         
@receiver(post_save, sender=Slot)
def remove_fills_with_on_overtime(sender, instance, **kwargs):
   if instance.week.slots.filter(
                  employee=instance.employee) \
                  .aggregate(Sum('shift__hours'))['shift__hours__sum'] >= 40:
                     
      for s in instance.week.slots.filter(fills_with=instance.employee).exclude(employee=instance.employee):
         s.fills_with.remove(instance.employee)

@receiver(post_save, sender=Workday)
def set_i_values(sender, instance, **kwargs):
   if instance.iweek == -1:
      instance.iweek = int(instance.date.strftime('%U'))
   if instance.iperiod == -1:
      instance.iperiod = int(instance.date.strftime('%U')) // 2
   if instance.ppd_id == -1:
      instance.ppd_id = (instance.schedule.start_date - instance.date).days + 1 % 14
   if instance.sd_id == -1:
      instance.sd_id = (instance.schedule.end_date - instance.date).days + 1
      

   