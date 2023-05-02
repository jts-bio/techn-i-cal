from django.contrib.auth.models import User
from main.models import Profile, Version, Workday, Slot, Shift, Schedule


from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal


import datetime as dt



@receiver(post_save, sender=Version)
def create_workdays(sender, instance, created, **kwargs):
    if created:
        for d in range(instance.schedule.department.schedule_week_count * 7):
                wd = Workday.objects.create(
                        date=instance.schedule.start_date + dt.timedelta(days=d), 
                        version=instance
                        )
                print (wd, 'created')

@receiver(pre_save, sender=Workday)
def set_workday_day_ids (sender, instance, **kwargs):
    if instance.sdid == 0:
        sdid = (instance.date - instance.version.schedule.start_date).days + 1
        wkid = (sdid - 1) // 7 + 1
        pdid = (wkid - 1) // 2 + 1

        instance.sdid = sdid
        instance.wkid = wkid
        instance.pdid = pdid

@receiver(pre_save, sender=Version)
def set_percent (sender, instance, **kwargs):
    slots_filled = Slot.objects.filter(workday__version=instance, employee__isnull=False).count()
    slots_total = Slot.objects.filter(workday__version=instance).count()
    if slots_total > 0:
        instance.percent = int(slots_filled / slots_total * 100)
    else:
        instance.percent = 0

@receiver(post_save, sender=Schedule)
def set_version_employees (sender, instance, created, **kwargs):
    if created:
        for e in instance.department.employees.filter(hire_date__lte=instance.start_date, active=True):
            instance.employees.add(e)
            print (e, 'added to', instance)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(post_save, sender=Workday)
def create_slots(sender, instance, created, **kwargs):
    if created:
        weekday = instance.weekday
        weekday = {"Sunday":"S","Monday":"M","Tuesday":"T","Wednesday":"W","Thursday":"R","Friday":"F","Saturday":"A"}[weekday]
        
        for s in Shift.objects.filter(
                    department= instance.version.schedule.department, 
                    weekdays__contains= weekday
            ):
                slot = Slot.objects.create(
                        workday=instance,
                        shift=s
                        )
                slot.save()



