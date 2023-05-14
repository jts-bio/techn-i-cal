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

from .subsignals.fill_candidate_signals import (
    add_fill_candidates,
)

from .subsignals.regulator_signals import (
    create_regulators,
)


@receiver(post_save, sender=Slot)
def clear_fills_with_on_conflicting_slot(sender, instance: Slot, **kwargs):
    if instance.employee is not None:
        for slot in instance.actions.conflicting_slots(instance):
            slot.fills_with.remove(instance.employee)


@receiver(post_save, sender=Slot)
def remove_employee_from_same_workday_fills(sender, instance, **kwargs):
    if instance.employee is not None:
        for slot in instance.workday.slots.exclude(pk=instance.pk).filter(fills_with=instance.employee):
            slot.fills_with.remove(instance.employee)


@receiver(pre_save, sender=Slot)
def remove_employee_from_assignments_on_same_workday(sender, instance, **kwargs):
    if instance.employee is not None:
        for assignment in instance.workday.slots.filter(employee=instance.employee).exclude(pk=instance.pk):
            assignment.employee = None


@receiver(post_save, sender=Slot)
def remove_fills_with_on_overtime(sender, instance, **kwargs):
    if instance.employee:
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


@receiver(post_save, sender=Slot)
def remove_fills_with_on_fte_met(sender, instance, **kwargs):
    """
    Remove employee from all slots.fills_with
    in a pay period once they have met their FTE
    """
    if instance.employee:
        if instance.week.slots \
                .filter(employee=instance.employee) \
                .aggregate(Sum('shift__hours'))['shift__hours__sum'] >= instance.employee.fte * 40:

            for s in instance.week.slots.filter(fills_with=instance.employee).exclude(employee=instance.employee):
                s.fills_with.remove(instance.employee)

@receiver(m2m_changed, sender=Slot.fill_candidates.through)
def annotate_if_fill_with_is_preferable(sender, instance, pk_set, **kwargs):
    """
    Annotate each employee in fills_with with if
    filling the slot with them would be preferable
    for the employee than their current assignment.
    """
    if pk_set:
        for emp_id in pk_set:

            employee = Employee.objects.get(pk=emp_id)
            shift_pref = employee.shift_prefs.filter(shift=instance.shift)

            if shift_pref.exists():
                shift_pref = shift_pref.first() # type: ShiftPreference

                if shift_pref.priority in ['P','SP']:
                    objs = instance.fills_with.through.objects.filter(
                        slot=instance,
                        employee=employee)
                    for obj in objs:
                        obj.preferable=True
                else:
                    objs = instance.fills_with.through.objects.filter(
                        slot=instance,
                        employee=employee)
                    for obj in objs:
                        obj.preferable=False

@receiver(pre_save, sender=Shift)
def assign_shift_slug (sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = instance.department.slug + '-' + instance.name.lower().replace(' ','-')