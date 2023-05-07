from .models import *
from django.db.models.signals import post_save, pre_save, m2m_changed, post_init
from django.dispatch import receiver, Signal
from django.db.models import Sum

from .subsignals.turnarounds import create_turnaround, delete_turnaround


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
         assignment.save()
         
@receiver(post_save, sender=Slot)
def remove_fills_with_on_overtime(sender, instance, **kwargs):
   if instance.week.slots.filter(employee=instance.employee).aggregate(Sum('shift__hours'))['shift__hours__sum'] >= 40:
      print('overtime-week-kill-switch signal fired')
      for s in instance.week.slots.filter(fills_with=instance.employee).exclude(employee=instance.employee):
         s.fills_with.remove(instance.employee)
