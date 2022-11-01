from .models import *
from django.db.models import Count, Sum, Subquery, OuterRef, F, Avg
import datetime as dt
import random 
import pandas as pd 

class WorkdayActions:

    def bulk_create (date_from: dt.date, date_to:dt.date) : 
        """
        Bulk create WORKDAYS for a range of dates.
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
        5. Dont fill if employee is working a different shift that day
        """
        templs = ShiftTemplate.objects.filter(ppd_id=workday.ppd_id) # type: ignore

        shifts = Shift.objects.filter(occur_days__contains=workday.iweekday) # type: ignore
        for shift in shifts:
            # dont overwrite existing slots:
            if Slot.objects.filter(workday=workday, shift=shift).exists()==False:
                if templs.filter(shift=shift).exists():
                    # dont fill if templated employee has a PTO request for day
                    if PtoRequest.objects.filter(employee=templs.get(shift=shift).employee, workday=workday.date).exists()==False:
                        # dont fill if employee already works that day:
                        if Slot.objects.filter(workday=workday, employee=templs.get(shift=shift).employee).exists()==False:
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

class WeekActions:
    
    def getAllWeekNumbers ():
        """
        Returns a list of all week numbers in the database
        """
        workdays = Workday.objects.all()
        week_numbers = []
        for workday in workdays:
            if (workday.date.year, workday.iweek) not in week_numbers:
                week_numbers.append((workday.date.year, workday.iweek))
        return week_numbers    
    
    def delSlotsLowPrefScores (year,week):
        """
        Delete slots from weeks where the assigned employee has a shift preference score below their average. 
        Purpose is to attempt refill, now with a more complete weekly schedule, and get avg shift pref scores higher.
        """
        workdays = Workday.objects.filter(date__year=year, iweek=week)
        slots = Slot.objects.filter(workday__in=workdays)
        slots = slots.belowAvg_sftPrefScore()
        for slot in slots:
            slot.delete()
        
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
    
    def get_unfavorables (year, sch):
        nfs = tally(list(
            Slot.objects.filter(
                shift__start__gt = dt.time(10,00),
                workday__ischedule = sch,
            ).values_list('employee__name',flat=True)))
        return nfs
    
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
    
    # ==== INTER-DAY SWAP FUNCTIONS ==== 
    
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
        print(best_swap)
        return best_swap  # ex: (slotA, slotB)

    def perform_swap (slotA, slotB):
        empA           = slotA.employee
        slotA.employee = slotB.employee
        slotA.save()
        slotB.employee = empA
        slotB.save()
        
        print("swapped %s,%s for %s,%s" %(slotA.shift,slotA.employee,slotB.shift,slotB.employee))
        
    def swaps_for_week (year, week):
        wds = Workday.objects.filter(date__year=year, iweek=week).order_by('date')
        for day in wds:
            pref_score = ScheduleBot.WdOverallShiftPrefScore(day)
            keep_trying = True
            while keep_trying == True:
                ScheduleBot.best_swap(day)
                if ScheduleBot.WdOverallShiftPrefScore(day) == pref_score:
                    keep_trying = False
        return None
       
    def del_turnarounds (year, sch): 
        slots = Slot.objects.filter(workday__year=year,workday__ischedule=sch, is_turnaround=True)
        for slot in slots:
            if slot.employee.evening_pref == False: 
                wd = slot.workday.prevWD()
                Slot.objects.get(workday=wd, employee=slot.employee).delete()
            else:
                slot.delete()
                
    # ==== INTER-WEEK SWAP FUNCTIONS ====
        
    def WdOverallShiftPrefScore (workday) -> int:
        """
        A Value describing the overall affinity of the shifts employees were assigned for that day. Higher score should
        mean employees on average are assigned to the shifts they like the most.
        """
        shifts              = Shift.objects.on_weekday(weekday=workday.iweekday)   # type: ignore
        slots               = Slot.objects.filter(workday=workday)
        for slot in slots:
            slot.save()
        shifts              = shifts.annotate(assign=Subquery(slots.filter(shift=OuterRef('pk')).values('employee')))
        shifts              = shifts.annotate(assignment=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__name')))
        # annotate shifts with whether that slot is a turnaround
        shifts              = shifts.annotate(
            is_turnaround=Subquery(slots.filter(shift=OuterRef('pk')).values('is_turnaround'))).annotate(
                prefScore=Subquery(ShiftPreference.objects.filter(shift=OuterRef('pk'), employee=OuterRef('assign')).values('score'))
            )
        if len(slots) != 0:
            overall_pref = int(shifts.aggregate(Sum(F('prefScore')))['prefScore__sum'] /(2 * len(slots)) *100)
        else:
            overall_pref = 0
        
        return overall_pref
       
    def streakPrefOk (workday) -> EmployeeManager :
        output = []
        empls = Employee.objects.all()
        for empl in empls:
            if PredictBot.predict_streak(empl,workday) <= empl.streak_pref:
                output.append (empl.pk)
        return Employee.objects.filter(pk__in=output)
    
    # ==== SCHEDULE =====
    
    def solveSchedule (yr,sch):
        
        wds = Workday.objects.filter(date__year=yr,ischedule=sch)
        
        for day in wds:
            WorkdayActions.fillDailySST(day)
        
        if len(wds) == 0:
            return False
        
        for day in wds:
            day.getshifts = Shift.objects.on_weekday(day.iweekday).exclude(slot__workday=day)
            day.slots     = Slot.objects.filter(workday=day)
        
        # put the list into a list of occurences in the form (workday, shift, number of employees who could fill this slot)
        unfilledSlots = [(day, shift, Employee.objects.can_fill_shift_on_day(shift=shift, workday=day).values('pk').count()) for day in wds for shift in day.getshifts]
        
        # sort this list by the number of employees who could fill the slot
        unfilledSlots.sort (key=lambda x: x[2])
        
        for slot in unfilledSlots:
            employees = Employee.objects.can_fill_shift_on_day(shift=slot[1],workday=slot[0])
            
            employee_lowest_fte_percent = [emp.ftePercForWeek(slot[0].date.year,slot[0].iweek) for emp in employees]
        
            if len(employees) != 0:
               # select lowest fte
                index     = employee_lowest_fte_percent.index(min(employee_lowest_fte_percent))
                empl      = employees[index]
                newSlot   = Slot.objects.create(workday=slot[0],shift=slot[1],employee=empl)
                newSlot.save() 
                
        for slot in Slot.objects.filter(is_turnaround=True, workday__iweekday__in=[1,2,3,4,5]):
        
            allinWeek       = Slot.objects.filter(workday__date__year=slot.workday.date.year,workday__iweek=slot.workday.iweek)
            daysWorked      = allinWeek.filter(employee=slot.employee).values('workday')
            dropDaysWork    = allinWeek.exclude(workday__in=daysWorked)
            dropUntrained   = dropDaysWork.filter(shift__in=slot.employee.shifts_trained.all())
            empAslots       = allinWeek.filter(employee=slot.employee).values('workday')
            dropOnDaysWorked = dropUntrained.exclude(workday__in=empAslots)
            #conflicting are Slots that create turnaround interference with the potential trade
            allconflicting  = []
            for s in Slot.objects.filter(pk__in=empAslots):
                allconflicting += Slot.objects.incompatible_slots(workday=s.workday,shift=s.shift)
            dropConflicting = dropOnDaysWorked.exclude(pk__in=allconflicting)
            possible        = dropConflicting

            pos = []
            
            for possibleSlot in possible:
                # check to make sure employeeB is trained for the shift they would be swapping into
                if possibleSlot.employee.shifts_trained.contains(slot.shift):
                    # dont include in possiblities if employeeB would be traded into a turnaround
                    if Slot.objects.incompatible_slots(workday=slot.workday,shift=slot.shift).filter(employee=possibleSlot.employee).exists():
                        pass
                    else:
                        if possibleSlot.workday.iweekday in [1,2,3,4,5]:
                            pos.append(possibleSlot)
                        
                        
            possibilities = []    
            for p in pos:
                if not ShiftTemplate.objects.filter(shift=p.shift,ppd_id=p.workday.ppd_id).exists():
                    possibilities.append(p)
            
            pos_choice = possibilities[random.randint (0,len(possibilities)-1)]
            
            
            slot_a     = slot
            slot_b     = pos_choice
            slotAEmpl  = slot_a.employee
            slotAWD    = slot_a.workday
            slotAShift = slot_a.shift
            slotBEmpl  = slot_b.employee
            slotBWD    = slot_b.workday
            slotBShift = slot_b.shift
            
            slot_a.delete()
            slot_b.delete()
            newA = Slot.objects.create(
                workday=slotAWD, shift=slotAShift, employee=slotBEmpl)
            newA.save()
            newB = Slot.objects.create(
                workday=slotBWD, shift=slotBShift, employee=slotAEmpl)
            newB.save()
            
            turnarounds  = Slot.objects.filter(workday__date__year=yr,workday__ischedule=sch, is_turnaround=True)
            for ta in turnarounds:
                if ta.employee.evening_pref == False: 
                    if Slot.objects.filter(workday__date=ta.workday.prevWD().date, employee=slot.employee,shift__start__hour__gt=10).exists():
                        Slot.objects.get(workday__date=ta.workday.prevWD().date, employee=slot.employee, shift__start__hour__gt=10).delete()
                    else:
                        ta.delete()
                else:
                    ta.delete()
                    
        week_nums = wds.values('iweek').distinct()
        
        for i in week_nums :
            ScheduleBot.performSolvingFunctionOnce (yr, i['iweek'])
            
class EmployeeBot:
    
    def get_emplUpcomingUnfavorables (employeeName):
        td = Workday.objects.get(date=dt.date.today())
        week0 = td.iweek
        weeks = range(week0, week0 + 6)
        return Slot.objects.filter(workday__iweek__in=weeks,workday__date__year=td.date.year, shift__start__hour__gte=10, employee__name=employeeName)
        
    
    def empScheduleHours (employeeName,year,sch):
        """Get #hrs an employee is scheduled for a particular schedule"""
        return sum(list(Slot.objects.filter(
            workday__ischedule=sch,workday__date__year=year,employee__name=employeeName).values_list('shift__hours',flat=True)))
        
    def empScheduleHoursByWeek (employeeName,year,sch):
        first_day   = Workday.objects.filter(date__year=year,ischedule=sch).first()
        week_nums   = range(first_day.iweek, first_day.iweek + 6)
        week_totals = []
        for week in week_nums:
            week_totals.append(sum(list(Slot.objects.filter(
                workday__iweek=week,workday__date__year=year,employee__name=employeeName).values_list('shift__hours',flat=True))))
        return week_totals
        
    def empScheduleHoursFtePercent (employeeName,year,sch):
        """Get a % Expected hours for a given schedule"""
        empl = Employee.objects.get(name=employeeName)
        if empl.fte == 0:
            return None
        total = EmployeeBot.empScheduleHours(employeeName,year,sch)
        return total / (empl.fte * 3 * 80)
    
class ShiftPrefBot :
    
    def make_avg_agg ():
        # annotate on employee -- get avg preference for each all shifts scored by an employee
        return Employee.objects.annotate(avgSftPref=Avg(Subquery(ShiftPreference.objects.filter(employee=OuterRef('pk')).values('score'),output_field=FloatField())))
        
    def slotsBelowEmplAvg ():
        # annotate on each slot -- get employee's avg and what their assigned shift's pref score is relative to that
        return Slot.objects.annotate(emplAvgSftPref=Subquery(ShiftPreference.objects.filter(employee=OuterRef('employee')).values('score'), output_field=FloatField()))
    
    def slotsOverStreakPref ():
        return Slot.objects.filter(isOverStreakPref=True)
                        
class ExportBot :
    
    def exportWeek (year,week):
        workdays = Workday.objects.filter(date__year=year, iweek=week).order_by('date')
        employees = Employee.objects.all()
        # Workdays will be Columns, Employees will be rows. Cell Values are shift names.
        # Create pandas DataFrame:
        df = pd.DataFrame(columns=workdays.values_list('date', flat=True))
        for emp in employees:
            df.loc[emp.name] = ''
        for i, workday in enumerate(workdays):
            for sl in Slot.objects.filter(workday=workday):
                df.loc[sl.employee.name][i] = sl.shift.name
        print(df)
        
    def exportPeriod(year,payperiod):
        workdays = Workday.objects.filter(date__year=year,iperiod=payperiod).order_by('date')
        employees = Employee.objects.all()
        df = pd.DataFrame(columns=workdays.values_list('date', flat=True))
        for emp in employees:
            df.loc[emp.name] = ''
        for i, workday in enumerate(workdays):
            for sl in Slot.objects.filter(workday=workday):
                df.loc[sl.employee.name][i] = sl.shift.name
        print(df)
        
    def scheduleForEmployee (employee):
        """ SCHEDULE FOR EMPLOYEE
        Shows Schedule for the next 42 Days
        ------------------------------------
        Example Output: 
        >>>     <WorkdayManager [{'empShift': 7}, {'empShift': None}]>
        """
        
        wds = Workday.objects.filter(date__gte=dt.date.today(), date__lte=dt.date.today() + dt.timedelta(days=42))
        return  wds.annotate(empShift=Subquery(Slot.objects.filter(employee=employee, workday=OuterRef('pk')).values('shift')))
      
class PredictBot :
    
    def predict_streak (employee, workday) -> int :
        if Slot.objects.filter(employee=employee, workday=workday).exists():
            streak = Slot.objects.get(employee=employee,workday=workday).streak 
            return streak + 1
        else :
            return 1
        
    def predict_createdStreak (employee, workday):
        
        if Slot.objects.filter(employee=employee,workday=workday.prevWD()).exists():
            if Slot.objects.filter(employee=employee,workday=workday.nextWD()).exists() == False:
                return Slot.objects.get(employee=employee,workday=workday.prevWD()).streak + 1
            elif Slot.objects.filter(employee=employee,workday=workday.nextWD()).exists():
                i = 1
                while Slot.objects.filter(employee=employee,workday__date=workday.date + dt.timedelta(days=i)).exists():
                    i += 1
                return Slot.objects.get(employee=employee,workday=workday.prevWD()).streak + 1 + i
        if Slot.objects.filter(employee=employee,workday=workday.prevWD()).exists() == False:
            return 1
        
class GhostSlot :
    
    def toExcludeTurnarounds (workday,shift):
        if shift.start.hour >= 10:
            return Slot.objects.filter(workday=workday.nextWD(),shift__start__hour__lte=10).values('employee__pk').distinct()
        if shift.start.hour < 10:
            return Slot.objects.filter(workday=workday.prevWD(),shift__start__hour__gte=10).values('employee__pk').distinct()
        
    def toExcludeSameDay (workday):
        return Slot.objects.filter(workday=workday).values('employee__pk').distinct()
    
    def toExcludeOvertime (workday,shift):
        empls = []
        for emp in Employee.objects.all():
            if emp.weekly_hours(workday.date.year,workday.iweek):
                if emp.weekly_hours(workday.date.year,workday.iweek) + shift.hours <= 40:
                    empls.append(emp.pk)
        return empls
    
    def toExcludeAvailability (shift):
        avail =  Employee.objects.filter(shifts_available=shift).values_list('pk',flat=True)
        return Employee.objects.exclude(pk__in=avail)
    
    def toExcludeTdoExists (workday):
        return TemplatedDayOff.objects.filter(sd_id=workday.sd_id).values('employee__pk').distinct()
    
    def toExcludePtoReqExists (workday):
        return PtoRequest.objects.filter(workday=workday.date,status__in=['P','A']).values('employee__pk').distinct()
    
    def fillList (workday,shift):
        empls = Employee.objects.all()
        fill = empls.exclude(pk__in=GhostSlot.toExcludeTurnarounds(workday,shift))
        fill = fill.exclude(pk__in=GhostSlot.toExcludeSameDay(workday))
        fill = fill.exclude(pk__in=GhostSlot.toExcludeOvertime(workday,shift))
        fill = fill.exclude(pk__in=GhostSlot.toExcludeAvailability(shift))
        fill = fill.exclude(pk__in=GhostSlot.toExcludeTdoExists(workday))
        fill = fill.exclude(pk__in=GhostSlot.toExcludePtoReqExists(workday))
        return fill
    