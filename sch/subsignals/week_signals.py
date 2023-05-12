from sch.models import Week
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Week)
def assign_version(sender, instance, **kwargs):
    if not instance.version:
        print("Assigning Version {instance.period.schedule.version} to week")
        instance.version = instance.period.schedule.version




