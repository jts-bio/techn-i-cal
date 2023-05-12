from sch.models import Week
from django.db.models.signals import post_save, post_init, pre_save 
from django.dispatch import receiver



@receiver(post_save, sender=Week)
def assign_version (sender, instance, created, **kwargs):
   if not instance.version:
      print("Assigning Version")
      instance.version = instance.period.schedule.version

