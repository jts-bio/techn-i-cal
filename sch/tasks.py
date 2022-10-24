from celery import shared_task 
from .models import *
from .actions import * 
import random 



@shared_task 
def performSolvingFunctionOnce (year, week):
        wds = Workday.objects.filter(date__year=year, iweek=week).order_by('date')
        if len(wds) == 0:
            return False
        for day in wds:
            day.getshifts = Shift.objects.on_weekday(day.iweekday).exclude(slot__workday=day)
            day.slots     = Slot.objects.filter(workday=day)
        # put the list into a list of occurences in the form (workday, shift, number of employees who could fill this slot)
        unfilledSlots = [(day, shift, Employee.objects.can_fill_shift_on_day(shift=shift, workday=day).values('pk').count()) for day in wds for shift in day.getshifts]
        # sort this list by the number of employees who could fill the slot
        unfilledSlots.sort(key=lambda x: x[2])
        if len(unfilledSlots) == 0:
            return False

        attempting_slot = 0
        
        while attempting_slot < 5 :
            if len(unfilledSlots) <= attempting_slot:
                return True
            slot = unfilledSlots[attempting_slot-1]
            # for each slot, assign the employee who has the least number of other slots they could fill
            day = slot[0]
            shift = slot[1]
            # pull out employees with no guaranteed hours
            prn_empls     = Employee.objects.filter(fte=0)
            empl          = Employee.objects.can_fill_shift_on_day(shift=shift, workday=day).annotate(n_slots=Count('slot')).order_by('n_slots')
            incompat_empl = Slot.objects.incompatible_slots(workday=day,shift=shift).values('employee')
            
            # don't schedule on opposite weekends 
            if day.iweekday == 0: 
                opp_weekend = Workday.objects.get(date=day.date+dt.timedelta(days=6)).filledSlots.values('employee')
                empl        = empl.exclude(pk__in=opp_weekend)
            if day.iweekday == 6:
                opp_weekend = Workday.objects.get(date=day.date-dt.timedelta(days=6)).filledSlots.values('employee')
                empl        = empl.exclude(pk__in=opp_weekend)
            # exclude pt employees who would cross their fte 
            wk_hours_pt = Employee.objects.filter(fte_14_day__lt=70).exclude(pk__in=prn_empls)
            for pt_emp in wk_hours_pt:
                weekly_hours= pt_emp.weekly_hours(day.date.year,day.iweek) 
                if weekly_hours:
                    if weekly_hours >= pt_emp.fte_14_day / 2 : 
                        empl = empl.exclude(pk=pt_emp.pk)
            
            empl = empl.exclude(pk__in=incompat_empl)
            empl = empl.exclude(pk__in=prn_empls)
            # try not to cross streak_pref thresholds
            underStreak = ScheduleBot.streakPrefOk(day)
            underStreak = Employee.objects.filter(pk__in=underStreak)
            
            if empl.filter(pk__in=underStreak).count() != 0:
                empl = empl.filter(pk__in=underStreak)
            
            if empl.count() == 0:
                attempting_slot += 1
            else: 
                rand = random.randint(0,int(empl.count()-1))
                empl = empl[rand]
                newslot = Slot.objects.create(workday=day, shift=shift, employee=empl)
                newslot.save()
                return True

@shared_task
def solve_week_slots (year, week):
        fx = True 
        n = 0
        while fx == True and n < 200 :
            fx = performSolvingFunctionOnce(year,week)
            n += 1
        