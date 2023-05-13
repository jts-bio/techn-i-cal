from sch.models import *
from django.db.models import Case, When, Subquery, OuterRef, BooleanField, Exists, F
from django.utils import timezone as tz
from django.http import HttpResponse


def solve_schedule(schid):
    """Solves Schedule with:
    ALGORITHM E
    ============
    (Beta model of the solving algorithm)
   """

    sch = Schedule.objects.get(slug=schid)
    n_init = sch.slots.empty().count()
    print(n_init)

    t_init = tz.now()

    init_data = dict(
        empty=sch.slots.empty().count(),
        mistemplated=sch.slots.mistemplated().count(),
        untrained=sch.slots.untrained().count(),
        pto_conflicts=sch.slots.pto_violations().count(),
        tdo_conflicts=sch.slots.tdo_violations().count(),
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

    week_hours_subquery = Slot.objects.filter(
        schedule=sch,
        workday__iweek=F('workday__iweek'),
        employee=OuterRef('pk')
    ).values('employee').annotate(
        weekhours=Sum('shift__hours')
    )

    period_hours_subquery = Slot.objects.filter(
        schedule=sch,
        employee=OuterRef('pk'),
        workday__iperiod=F('workday__iperiod'),
    ).values('employee').annotate(
        periodhours=Sum('shift__hours')
    )

    pto_request_subquery = PtoRequest.objects.filter(
        employee=OuterRef('pk'),
        workday=OuterRef('workday__date')
    ).values('employee')[:1]

    empty_slots = sch.slots.empty().annotate(
                has_ptorequest=Exists(pto_request_subquery)
            ).annotate(
                weekhours=Subquery(week_hours_subquery,
                                   output_field=FloatField())
            ).annotate(
                periodhours=Subquery(period_hours_subquery,
                                     output_field=FloatField())
            ).annotate(
                needed_week_hours=F('employee__std_wk_max') - F('weekhours')
            ).exclude(
                pk__in=Subquery(prev_evening_subquery).bitor(
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
            ).values('employee')

    print(
        "N Empty Slots: "
        f"{empty_slots.count()}"
        )
    for slot in empty_slots.order_by('?'):

        who_can_fill = slot.shift.available.annotate(
            has_ptorequest=Exists(pto_request_subquery)
        ).annotate(
            weekhours=Subquery(week_hours_subquery,
                               output_field=FloatField())
        ).annotate(
            periodhours=Subquery(period_hours_subquery,
                                 output_field=FloatField())
        ).annotate(
            needed_week_hours=F('employee__std_wk_max') - F('weekhours')
        ).exclude(
            pk__in=Subquery(prev_evening_subquery).bitor(
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
        ).values('employee')

        if who_can_fill.exists():
            slot.employee = who_can_fill[0].order_by('-needed_week_hours').employee

    t_final = tz.now()
    t = t_final - t_init

    n_final = sch.slots.empty().count()
    n = n_init - n_final

    sch.routine_log.add(
        "SOLVE-BETA-ALGORITHM",
        "Beta model of the solving algorithm",
        dict(
                t=t.total_seconds(),
                n=n,
                **init_data
            )
    )

    return HttpResponse(f'Completed in {t.total_seconds()}')
