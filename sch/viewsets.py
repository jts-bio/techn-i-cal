from sch.models import *
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.contrib import messages


class Actions:
    class SlotActions:
        def clear_employee (request, slotId):
            if request.method == "POST":
                slot = Slot.objects.get(pk=slotId)
                slot.employee = None
                slot.save()
                messages.success(request, f"Success! {slot.workday}-{slot.shift} Assignment Cleared")
                return HttpResponseRedirect( slot.workday.url() )
            
            messages.error(request,"Error: Clearing the employee assignment on this slot was unsuccessful...")
            return HttpResponseRedirect (slot.url())
        
        def fill_with_best (request, slotId):
            if request.method == "POST":
                slot = Slot.objects.get(pk=slotId)
                empl_original = slot.employee
                slot.fillWithBestChoice()
                if slot.employee != empl_original:
                    msg = f"""Success! 
                    {slot.workday}-{slot.shift} Assigned to {slot.employee} 
                    via [FILL-VIA-BESTCHOICE]"""
                    messages.success(request,msg)
                    return HttpResponseRedirect(slot.workday.url())
                else:
                    msg = f"""No Change: 
                    {slot.workday}-{slot.shift} Assigned to {slot.employee} 
                    via [FILL-VIA-BESTCHOICE]"""
                    messages.success(request,msg)
                    return HttpResponseRedirect(slot.workday.url())
            
    class PeriodActions:
        def fill_slot_with_lowest_hour_employee (request, prdId):
            period = Period.objects.get(pk=prdId)
            empl = list(period.needed_hours())[0]
            fillableSlots = []
            for emptySlot in period.slots.empty():
                if empl in emptySlot.fillable_by():
                    fillableSlots += [emptySlot]
            selectedSlot = fillableSlots[random.randint(0,len(fillableSlots))]
            selectedSlot.employee = empl
            selectedSlot.save()
            if selectedSlot.employee != None:
                messages.success(request, f"Success: {selectedSlot} filled via PeriodActions.fill_slot_with_lowest_hour_employee")
            return HttpResponseRedirect (period.url())
            
    
class WeekViews:
    def all_slots_fillable_by_view (request, weekId):
        html_template = 'sch2/week/all-slots-fillable-by-view.html'
        week = Week.objects.get(pk=weekId)
        context = {
            'week':week,
        }
        return render(request,html_template,context)
    




class IdealFill:
    def levelA (request, slot_id):
        """Checks Training and No Turnarounds"""
        slot = Slot.objects.get(pk=slot_id)
        base_avaliable = slot.shift.available.all()
        inConflictingSlots = slot._get_conflicting_slots().values('employee')
        available__noConflict = base_avaliable.exclude(pk__in=inConflictingSlots)
        return available__noConflict
        
    def levelB (request, slot_id):
        """Checks for No Weekly Overtime"""
        slot = Slot.objects.get(pk=slot_id)
        underFte = []
        nh = slot.period.needed_hours()
        for n in nh:
            if nh[n] > slot.shift.hours:
                underFte += [n.pk]
        possible = IdealFill.levelA(None, slot_id)
        return possible.filter(pk__in=nh)
    
    def levelC (request, slot_id):
        """Checks for No PayPeriod FTE overages"""
        slot = Slot.objects.get(pk=slot_id)
        underFte = []
        nh = slot.week.needed_hours()
        for n in nh:
            if nh[n] > slot.shift.hours:
                underFte += [n.pk]
        possible = IdealFill.levelA(None, slot_id)
        return possible.filter(pk__in=nh)
        
    def levelD (request,slot_id):
        """Checks for Matching Time-of-day Preference"""
        slot = Slot.objects.get(pk=slot_id)
        timeGroup = slot.shift.group 
        possible = IdealFill.levelC(None, slot_id)
        return possible.filter(time_pref=timeGroup)
        
    def levelE (request, slot_id): 
        """Checks for Prefered Streak-length not to be exceeded"""
        slot = Slot.objects.get(pk=slot_id)
        possible = IdealFill.levelD(None, slot_id)
        okstreak = []
        for possibleEmpl in possible:
            slot.employee = possibleEmpl
            slot.save()
            maxStreak = slot.siblings_streak().count() + 1
            if slot.employee.streak_pref >= maxStreak:
                okstreak += [possibleEmpl]
        return Employee.objects.filter(pk__in=okstreak)
    
    def levelF (request,slot_id):
        for empl in IdealFill.levelE(None, slot_id):
            empl.shift