from .models import *
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.contrib import messages



class Actions : 
    
    class SlotActions :
        
        def clear_slot_assignment (request, slotPk):
            """CLEAR SLOT ASSIGNMENTS 
            ====================================================
            Successful POST will clear a slot's employee assigned to `NONE`
            """
            slot = Slot.objects.get(pk=slotPk)
            workday = slot.workday
            
            if request.method == "POST":
                slot.employee = None
                slot.save()
                MSG = "Success! This Slot was successfully cleared: Employee set to [NONE]"
                messages.success(request, MSG)
            
            else:
                MSG = "Error: This Slot Assignment could not be cleared..."
                messages.error (request, MSG)    
            
            return HttpResponseRedirect (workday.url())
        