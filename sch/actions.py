from .models import Shift, Employee, Workday, Slot, ShiftTemplate, PtoRequest, ShiftPreference
import datetime as dt


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
        
        
