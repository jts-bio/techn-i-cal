
from sch.models import Schedule, Employee
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver


@receiver(post_init, sender=Schedule)
def add_employees(sender, instance, created, **kwargs):
    if created:
        empls = Employee.objects.filter(department=instance.department,
                                        start_date__lte=instance.date,
                                        is_active=True)
        instance.add_employees(empls)