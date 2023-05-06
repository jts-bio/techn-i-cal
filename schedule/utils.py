from django.db.models import Case, CharField, Value, When
from django.db.models.functions import Coalesce
from sch.models import Schedule, Workday, Employee, Slot, PtoRequest
from typing import Tuple, Dict


def get_undertime_triplet (
         schid:Schedule|str, 
         empid:Employee|str
         ) -> Tuple[int,int,int]:
   
   """Undertime Triplet
   ====================
   An Undertime Triplet is a set of 3 ints,
   each representing the number of hours the 
   employee is underscheduled.
   
   examples:
   >>> Josh (0,0,20)      means Josh is underscheduled 20 hours during the 3rd pay period.
   
   >>> Brittanie (0,0,0)  means Brittanie is fully scheduled.
   """
   if isinstance(empid, str):
      empl = Employee.objects.get(slug=empid)
   elif isinstance(empid, Employee):
      empl = empid
   if isinstance(schid, str):
      sch = Schedule.objects.get(slug=schid)
   elif isinstance(schid, Schedule):
      sch = schid
   
   triplet = ()

   for p in range(3):
      phours = empl.fte * 80
      for w in range(2):
         for wd in sch.periods.all()[p].weeks.all()[w].workdays.all():
            if wd.slots.filter(employee=empl).count() > 0:
               phours -= wd.slots.filter(employee=empl).first().shift.hours
            elif PtoRequest.objects.filter(employee=empl, workday=wd.date).count() > 0:
               phours -= empl.pto_hrs
      if phours < 0:
         phours = 0
         
      triplet += (int(phours),)
      
   return triplet
   
def get_all_undertime_triplets(
         schid:Schedule|str
         ) -> Dict[Employee,Tuple[int,int,int]]:
   
   if isinstance(schid, str):
      sch = Schedule.objects.get(slug=schid)
   elif isinstance(schid, Schedule):
      sch = schid
      
   triplets = {}
   for empl in sch.employees.all():
      triplets[empl] = get_undertime_triplet(sch, empl)
      
   return triplets

def get_sum_sch_undertime (
         schid:Schedule|str
         ) -> int:
   
   if isinstance(schid, str):
      sch = Schedule.objects.get(slug=schid)
   elif isinstance(schid, Schedule):
      sch = schid
      
   total = 0
   triplets = get_all_undertime_triplets(sch)
   
   for triplet in triplets.values():
      total += sum(triplet)
      
   return total