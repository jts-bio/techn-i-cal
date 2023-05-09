from sch.models import *
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Slot)
def create_turnaround(sender, instance, **kwargs):
   if instance.employee != None:
      conflicting = instance._get_conflicting_slots().filter(employee=instance.employee).exclude(workday=instance.workday)
      if conflicting.exists():
         involved_slots = Slot.objects.filter(pk__in=[conflicting.first().pk, instance.pk])
         turnaround = Turnaround.objects.create(
                           employee=instance.employee, 
                           schedule=instance.schedule,
                           early_slot=involved_slots.first(),
                           late_slot=involved_slots.last(),
                           )
         turnaround.save()
         
         
@receiver(post_save, sender=Slot)
def delete_turnaround(sender, instance, **kwargs):
   if instance.employee == None:
      Turnaround.objects.filter(early_slot=instance).delete()
      Turnaround.objects.filter(late_slot=instance).delete()
   if instance.employee != None:
      conflicting = instance._get_conflicting_slots().filter(employee=instance.employee).exclude(workday=instance.workday)
      if not conflicting.exists():
         Turnaround.objects.filter(early_slot=instance).delete()
         Turnaround.objects.filter(late_slot=instance).delete()
   