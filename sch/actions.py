from .models import Shift, Employee, Workday, Slot, ShiftTemplate
import datetime as dt


class WorkdayActions:

    # def fillDailyTSS (workday) :
    #     templates = ShiftTemplate.objects.filter(ppd_id=workday.period_template_id)
    #     for template in templates:
    #         if Slot.objects.filter(workday=workday, shift=template.shift).exists()==False:
    #             slot = Slot.objects.create(workday=workday, shift=template.shift, employee=template.employee)
    #             slot.save()

    def bulk_create (date_from: dt.date, date_to:dt.date) : # type: ignore
        date = date_from
        while date <= date_to:
            if Workday.objects.filter(date=date).exists()==False:
                workday = Workday.objects.create(date=date)
                workday.save()
                # WorkdayActions.fillDailyTSS(workday)
            date = date + dt.timedelta(days=1) 

    def fillDailySST (workday) : # type: ignore
        templs = ShiftTemplate.objects.filter(ppd_id=workday.ppd_id) # type: ignore

        shifts = Shift.objects.filter(occur_days__contains=workday.iweekday) # type: ignore
        for shift in shifts:
            if Slot.objects.filter(workday=workday, shift=shift).exists()==False:
                if templs.filter(shift=shift).exists():
                    slot = Slot.objects.create(workday=workday, shift=shift, employee=templs.get(shift=shift).employee)
                    slot.save()

            
        