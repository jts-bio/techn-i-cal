from .models import Shift, Employee, Workday, Slot, ShiftTemplate



class WorkdayActions:

    def fillDailyTSS (workday) :
        templates = ShiftTemplate.objects.filter(ppd_id=workday.period_template_id)
        for template in templates:
            if Slot.objects.filter(workday=workday, shift=template.shift).exists()==False:
                slot = Slot.objects.create(workday=workday, shift=template.shift, employee=template.employee)
                slot.save()
            
        