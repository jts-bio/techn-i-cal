from sch.models import *
from django.db.models import Case, When, Subquery, OuterRef, BooleanField, Exists, F
from django.utils import timezone as tz




def solve_schedule(schid):
   """
   Solves Schedule with:
      ALGORITHYM E 
      (Beta model of the solving algorithm)
   """
   
   sch = Schedule.objects.get(slug=schid)
   
   t_init = tz.now()
   
   init_data = dict(
            empty= sch.slots.empty().count(),
            mistemplated= sch.slots.mistemplated().count(),
            untrained= sch.slots.untrained().count(),
            pto_conflicts= sch.slots.pto_violations().count(),
            tdo_conflicts= sch.slots.tdo_violations().count(),
         )
      
   sch.slots.untrained().update(employee=None)
   sch.slots.mistemplated().update(employee=None)
   sch.slots.pto_violations().update(employee=None)
   sch.slots.tdo_violations().update(employee=None)
   

   on_workday_subquery = Slot.objects.filter(  
            workday=F('workday__date')
            ).values('employee')[:1]
   
   prev_evening_subquery = Slot.objects.filter(
            schedule=sch,
            workday__date=F('workday__date') - dt.timedelta(days=1),
            shift__phase__gte=2
            ).values('employee')[:1]
   
   next_morning_subquery = Slot.objects.filter(
            schedule=sch,
            workday__date=F('workday__date') + dt.timedelta(days=1),
            shift__phase__gte=2
            ).values('employee')[:1]
   
   weekhours_subquery = Slot.objects.filter(
            schedule=sch,
            workday__iweek=F('workday__iweek'),
            employee=OuterRef('pk')
         ).values('employee').annotate(
            weekhours=Sum('shift__hours')
         )

   periodhours_subquery = Slot.objects.filter(
            schedule=sch,
            employee=OuterRef('pk'),
            workday__iperiod=F('workday__iperiod'),
         ).values('employee').annotate(
            periodhours=Sum('shift__hours')
         )
         
   ptorequest_subquery = PtoRequest.objects.filter(
            employee=OuterRef('pk'),
            workday=OuterRef('workday__date')
         ).values('employee')[:1]

   empty_slots = sch.slots.filter(
            template_employee__isnull=False,
            employee=None
               ).annotate(
            has_ptorequest=Exists(ptorequest_subquery)
               ).annotate(
            weekhours=Subquery(weekhours_subquery, 
                              output_field=FloatField())
               ).annotate(
            periodhours=Subquery(periodhours_subquery, 
                              output_field=FloatField())
               ).exclude(
            pk__in=Subquery(prev_evening_subquery ).bitor(
                   Subquery(next_morning_subquery)).bitor(
                   Subquery(on_workday_subquery))
               ).exclude(
            Case(
               When(
                  has_ptorequest=True, 
                  then=True
                  ),
               default=False,
               output_field=BooleanField()
            )
         )
            
   for slot in sch.slots.filter(
               template_employee__isnull=False,
               employee=None
                  ):
         
      who_can_fill = slot.shift.available.annotate(
               has_ptorequest=Exists(ptorequest_subquery)
            ).annotate(
               weekhours=Subquery(weekhours_subquery, 
                                 output_field=FloatField())
            ).annotate(
               periodhours=Subquery(periodhours_subquery, 
                                 output_field=FloatField())
            ).exclude(
               pk__in=Subquery(prev_evening_subquery ).bitor(
                     Subquery(next_morning_subquery)).bitor(
                     Subquery(on_workday_subquery)) 
            ).exclude(
               Case(
                  When(
                     has_ptorequest=True, 
                     then=True
                     ),
                  default=False,
                  output_field=BooleanField()
               )
            )
      
      if who_can_fill.exists():
         
            slot.employee = who_can_fill[0].employee
            
            
   t_final = tz.now()
   t = t_final - t_init
   
   sch.routine_log.add(
      "SOLVE-BETA-ALGORITHM",
      "Beta model of the solving algorithm",
      dict(t=t, **init_data)
   )
   
   return init_data, sch
      