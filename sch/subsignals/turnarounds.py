from sch.models import *
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Slot)
def create_turnaround(sender, instance, **kwargs):
   if instance.employee != None:
      conflicting = instance._get_conflicting_slots().filter(employee=instance.employee).exclude(workday=instance.workday)
      if conflicting.exists():
         turnaround = Turnaround.objects.create(employee=instance.employee, schedule=instance.schedule)
         turnaround.slots.add(instance)
         turnaround.slots.add(conflicting.first())
         
@receiver(post_save, sender=Slot)
def delete_turnaround(sender, instance, **kwargs):
   if instance.employee != None:
      conflicting = instance._get_conflicting_slots().filter(employee=instance.employee).exclude(workday=instance.workday)
      if not conflicting.exists():
         Turnaround.objects.filter(slots=instance).delete()