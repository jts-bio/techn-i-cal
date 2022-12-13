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
                slot.fillWithBestChoice()
                slot.save()
                messages.success(request, f'Success! {slot.workday}-{slot.shift} Assigned to {slot.employee} via [FILL-VIA-BESTCHOICE]')
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