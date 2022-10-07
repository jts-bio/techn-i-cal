from .models import Shift, Employee, Workday, Slot, ShiftTemplate, PtoRequest, ShiftPreference
from django.db.models import Count
import datetime as dt
import random 


class WorkdayActions:

    def bulk_create (date_from: dt.date, date_to:dt.date) : 
        """
        Bulk create workdays for a range of dates.
        """
        date = date_from
        while date <= date_to:
            if Workday.objects.filter(date=date).exists()==False:
                workday = Workday.objects.create(date=date)
                workday.save()
                # WorkdayActions.fillDailyTSS(workday)
            date = date + dt.timedelta(days=1) 

    def fillDailySST (workday) : # type: ignore
        """
        Run the necessary checks and, when appropriate, fill slots with
        Shift-Slot-Templates.

        Checks:
        1. No existing slot 
        2. Template exists for the day
        3. Employee Templated is not on PTO.
        4. Dont fill an employee into a turnaround 
        #TODO Dont fill if employee is working a different shift that day
        """
        templs = ShiftTemplate.objects.filter(ppd_id=workday.ppd_id) # type: ignore

        shifts = Shift.objects.filter(occur_days__contains=workday.iweekday) # type: ignore
        for shift in shifts:
            # dont overwrite existing slots:
            if Slot.objects.filter(workday=workday, shift=shift).exists()==False:
                if templs.filter(shift=shift).exists():
                    # dont fill if templated employee has a PTO request for day
                    if PtoRequest.objects.filter(employee=templs.get(shift=shift).employee, workday=workday.date).exists()==False:
                        # avoid creating a turnaround
                        if shift.start < dt.time(12):
                            if Slot.objects.filter(workday=workday.prevWD(), employee=templs.get(shift=shift).employee, shift__start__gt=dt.time(12)).exists()==False:
                                slot = Slot.objects.create(workday=workday, shift=shift, employee=templs.get(shift=shift).employee)
                                slot.save()
                        # avoid creating a preturnaround
                        elif shift.start > dt.time(12):
                            if Slot.objects.filter(workday=workday.nextWD(), employee=templs.get(shift=shift).employee, shift__start__lt=dt.time(12)).exists()==False:
                                slot = Slot.objects.create(workday=workday, shift=shift, employee=templs.get(shift=shift).employee)
                                slot.save()

    def identifySwaps (workday) :
        slots = Slot.objects.filter(workday=workday)
        for slot in slots:
            empl = slot.employee
            print(empl)
            if ShiftPreference.objects.filter(employee=empl, shift=slot.shift).exists() == False:
                break
            currentScore = ShiftPreference.objects.get(employee=empl, shift=slot.shift).score
            print("currentScore",currentScore)
            moreFavorables = ShiftPreference.objects.filter(employee=empl,score__gt=currentScore)
            # exclude moreFavorables that don't occur on this weekday:
            moreFavorables = moreFavorables.filter(shift__occur_days__contains=workday.iweekday)
            print("moreFavorables", [mf.shift for mf in moreFavorables])
            for mf in moreFavorables:
                if Slot.objects.filter(workday=workday, shift=mf.shift).exists():
                    incumbentEmpl = Slot.objects.get(workday=workday, shift=mf.shift).employee
                    incumbentCurrentScore = ShiftPreference.objects.get(employee=incumbentEmpl, shift=mf.shift).score
                    incumbentHypoScore = ShiftPreference.objects.get(employee=incumbentEmpl, shift=slot.shift).score
                    if incumbentHypoScore > incumbentCurrentScore:
                        # do swap
                        slot.employee = incumbentEmpl
                        slot.save()
                        other_slot = Slot.objects.get(shift=mf.shift, workday=workday)
                        other_slot.employee = empl
                        other_slot.save()
                
            # if ShiftPreference.objects.filter(employee=empl, shift=slot.shift).exists():
            #     currentScore = ShiftPreference.objects.get(employee=empl, shift=slot.shift).score
            #     moreFavorables = ShiftPreference.objects.filter(employee=empl, score__gt=currentScore)
            #     if moreFavorables.exists():
            #         for mf in moreFavorables:
            #             currentOccupant = Slot.objects.get(workday=workday, shift=mf.shift).employee
            #             if ShiftPreference.objects.filter(employee=currentOccupant, shift=mf.shift).exists():
            #                 currentOccScore = ShiftPreference.objects.get(employee=currentOccupant, shift=mf.shift).score
            #                 if ShiftPreference.objects.filter(employee=currentOccupant, shift=slot.shift).exists():
            #                     currentOccSwapScore = ShiftPreference.objects.get(employee=currentOccupant, shift=slot.shift).score
            #                     if currentOccSwapScore > currentOccScore:
            #                         if Slot.objects.get(workday=workday, shift=mf.shift).employee != empl:
            #                             Slot.objects.filter(workday=workday, shift=slot.shift).update(employee=Slot.objects.get(workday=workday, shift=mf.shift).employee)
            #                             Slot.objects.filter(workday=workday, shift=mf.shift).update(employee=empl)

class WeekActions:
    def getAllWeekNumbers ():
        """
        Returns a list of all week numbers in the database
        """
        workdays = Workday.objects.all()
        week_numbers = []
        for workday in workdays:
            if (workday.date.year, workday.iweek) not in week_numbers:
                week_numbers.append(workday.week_number)
        return week_numbers
            
        
class PayPeriodActions:
    def getPeriodFtePercents (year,pp):
        employees = Employee.objects.filter(fte__gt=0)
        slots = Slot.objects.filter(workday__date__year=year,workday__iperiod=pp)
        for emp in employees:
            emp.period_fte_percent = int((sum(list(slots.filter(employee=emp).values_list('shift__hours',flat=True))) / emp.fte_14_day) * 100)

        return employees
    
    def getWorkdayPercentCoverage (workday):
        """
        Returns the percent coverage of a workday.
        """
        slots = Slot.objects.filter(workday=workday).count()
        shifts = Shift.objects.filter(occur_days__contains=workday.iweekday).count()
        return int((slots/shifts)*100)
    
    
class ScheduleBot:
    
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
        
        slot = unfilledSlots[0]
        # for each slot, assign the employee who has the least number of other slots they could fill
        day = slot[0]
        shift = slot[1]
        # pull out employees with no guaranteed hours
        prn_empls = Employee.objects.filter(fte=0)
        empl = Employee.objects.can_fill_shift_on_day(shift=shift, workday=day).annotate(n_slots=Count('slot')).order_by('n_slots')
        incompat_empl = Slot.objects.incompatible_slots(workday=day,shift=shift).values('employee')
        empl = empl.exclude(pk__in=incompat_empl)
        empl = empl.exclude(pk__in=prn_empls)
        if empl.count() == 0:
            return False
        rand = random.randint(0,int(empl.count()/2))
        empl = empl[rand]
        newslot = Slot.objects.create(workday=day, shift=shift, employee=empl)
        newslot.save()
        return True
    
    def getWhoCanFillShiftOnWorkday (shift, workday):
        """
        Returns a list of employees who can fill a shift on a workday.
        """
        return Employee.objects.can_fill_shift_on_day(shift=shift, workday=workday)
    
    def getMinSolutionsSlot (year,week=0,period=0):
        """
        Returns the slot with the most problems.
        """
        if week != 0:
            slots = Slot.objects.filter(workday__year=year,workday__iweek=week)
        elif period != 0:
            slots = Slot.objects.filter(workday__year=year,workday__iperiod=period)
        # get shift list by day of week
        shift_list = [Shift.objects.filter(occur_days__contains=i) for i in range(7)]
        
    def is_agreeable_swap (slotA, slotB):
        employeeA = slotA.employee
        if ShiftPreference.objects.filter(employee=employeeA, shift=slotA.shift).exists():
            scoreA = ShiftPreference.objects.get(employee=employeeA, shift=slotA.shift).score 
        else:
            return None 
        if ShiftPreference.objects.filter(employee=employeeA, shift=slotB.shift).exists():
            scoreA_trade = ShiftPreference.objects.get(employee=employeeA, shift=slotB.shift).score  
        else:
            return None
        if Slot.objects.incompatible_slots(shift=slotB.shift, workday=slotB.workday).filter(employee=employeeA).exists():
            return None 
        employeeB = slotB.employee
        if employeeB.available_for(shift=slotA.shift) == False:
            print(employeeB.available_for(shift=slotA.shift))
            return None
        if ShiftPreference.objects.filter(employee=employeeB, shift=slotB.shift).exists():
            scoreB = ShiftPreference.objects.get(employee=employeeB, shift=slotB.shift).score 
        else:
            return None
        if ShiftPreference.objects.filter(employee=employeeB, shift=slotA.shift).exists():
            scoreB_trade = ShiftPreference.objects.get(employee=employeeB, shift=slotA.shift).score 
        else:
            return None
        if Slot.objects.incompatible_slots(shift=slotA.shift, workday=slotA.workday).filter(employee=employeeB).exists():
            return None 
        if scoreA_trade >= scoreA and scoreB_trade > scoreB:
            return {(slotA, slotB) : (scoreA_trade - scoreA) + (scoreB_trade - scoreB)}
        else:
            return None
        
    def best_swap (workday):
        slots = Slot.objects.filter(workday=workday)
        swaps = {}
        for slota in slots:
            for slotb in slots:
                if slota != slotb:
                    swap = ScheduleBot.is_agreeable_swap(slota,slotb)
                    if swap != None:
                        swaps.update(swap)
        if swaps == {}:
            return None
        best_swap = max(swaps, key=swaps.get)
        return best_swap

    def perform_swap (slotA, slotB):
        empA = slotA.employee
        slotA.employee = slotB.employee
        slotA.save()
        slotB.employee = empA
        slotB.save()
        print("swapped %s,%s for %s,%s" %(slotA.shift,slotA.employee,slotB.shift,slotB.employee))