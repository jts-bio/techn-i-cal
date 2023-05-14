from sch.models import Schedule, Employee, FillCandidate, Slot
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver



@receiver(post_save, sender=Slot)
def add_fill_candidates(sender, instance, created, **kwargs):
    if not instance.fill_candidates.exists():
        empls = instance.schedule.employees.all() \
                    .exclude(pk__in=instance.workday.on_pto()) \
                    .exclude(pk__in=instance.workday.on_tdo()) \
                    .filter(available=instance)
        instance.fill_candidates.add(*empls)


