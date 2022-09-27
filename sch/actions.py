from .models import Shift, Employee, Workday, Slot, ShiftTemplate, PtoRequest
import datetime as dt


class WorkdayActions:

    def bulk_create (date_from: dt.date, date_to:dt.date) : # type: ignore
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
        
        # TODO: Dont fill an employee into a turnaround 
        
        """
        templs = ShiftTemplate.objects.filter(ppd_id=workday.ppd_id) # type: ignore

        shifts = Shift.objects.filter(occur_days__contains=workday.iweekday) # type: ignore
        for shift in shifts:
            # dont overwrite existing slots:
            if Slot.objects.filter(workday=workday, shift=shift).exists()==False:
                if templs.filter(shift=shift).exists():
                    # dont fill if templated employee has a PTO request for day
                    if PtoRequest.objects.filter(employee=templs.get(shift=shift).employee, workday=workday.date).exists()==False:
                        slot = Slot.objects.create(workday=workday, shift=shift, employee=templs.get(shift=shift).employee)
                        slot.save()

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
            
        