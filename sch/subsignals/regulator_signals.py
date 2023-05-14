from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver
from django.db.models import Q, Sum
from sch.models import Schedule, Employee, FillCandidate, Slot, Workday, Period, PeriodRegulator


@receiver(post_save, sender=Period)
def create_regulators(sender, instance, created, **kwargs):
    if created:
        for empl in instance.schedule.employees.all():
            if empl.fte == 0:
                if empl in instance.schedule.data['maxes']:
                    if instance.schedule.data['maxes'][empl] != 0:
                        goal = instance.schedule.data['maxes'][empl]
            else:
                goal = empl.std_wk_max
            reg = PeriodRegulator.objects.create(period=instance, employee=empl, goal_hours=goal)
            reg.save()


@receiver(pre_save, sender=Slot)
def check_employee_change(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        if instance.employee is not None:  # Object is new and assigned to an Employee
            print(f'Employee {instance.employee.name} added to slot')
            reg = PeriodRegulator.objects.filter(period=instance.week.period, employee=obj.employee)
            if not reg.exists():
                return
            reg = reg.first()
            prd = instance.week.period
            reg.hours = prd.slots.filter(employee=obj.employee).aggregate(Sum('shift__hours'))['shift__hours__sum']
    else:
        if instance.employee != obj.employee: # compare the instance field with the current database value
            if instance.employee is None:
                print(f'Employee {obj.employee.name} removed from slot')
                reg = PeriodRegulator.objects.filter(period=instance.week.period, employee=obj.employee)
                if not reg.exists():
                    return
                reg = reg.first()
                prd = instance.week.period
                reg.hours = prd.slots.filter(employee=obj.employee).aggregate(Sum('shift__hours'))['shift__hours__sum']
            else:
                print(f'Employee for Slot {instance.id} was changed from {obj.employee} to {instance.employee}')
                reg = PeriodRegulator.objects.filter(period=instance.week.period, employee=obj.employee)
                if not reg.exists():
                    return
                reg = reg.first()
                prd = instance.week.period
                reg.hours = prd.slots.filter(employee=obj.employee).aggregate(Sum('shift__hours'))['shift__hours__sum']
