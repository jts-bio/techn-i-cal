from sch.models import *

js = Employee.objects.get(name="JOSH")

js.streak_pref
`3`

js.fte
`0.625`

js.url()
`'/sch/employee/JOSH/'`

js.trained_for(Shift.objects.get(name='RS'))
`<ShiftManager [<Shift: 3>]>`

js.shifts_trained.all()
```
<ShiftManager [<Shift: MI>, <Shift: 7C>, <Shift: 7P>, <Shift: S>, <Shift: OP>, <Shift: EI>, <Shift: EP>, <Shift: 3>, <Shift: N>]>
```

js.templated_days
<QuerySet [<ShiftTemplate: MonA:S Template>, <ShiftTemplate: TueA:S Template>, <ShiftTemplate: ThuB:S Template>]>

js.templated_days.count()
3

js
<Employee: JOSH>
js.count_shift_occurances()
<SlotManager [{'shift__name': '7C', 'count': 6}, {'shift__name': '7P', 'count': 1}, {'shift__name': 'EI', 'count': 7}, {'shift__name': 'EP', 'count': 3}, {'shift__name': 'MI', 'count': 2}, {'shift__name': 'N', 'count': 1}, {'shift__name': 'OP', 'count': 3}, {'shift__name': 'S', 'count': 25}]>

Week.objects.all()
<QuerySet []>

Workday.objects.all().first()
<Workday: 2022 01 01>

Workday.objects.all().last()
<Workday: 2023 01 01>

Slot.objects.filter(employee=js, is_terminal=True)
<SlotManager [<Slot: 2022 11 15 S>, <Slot: 2022 09 29 S>, <Slot: 2022 09 26 EP>, <Slot: 2022 10 01 EI>, <Slot: 2022 12 08 S>, <Slot: 2022 12 05 EI>, <Slot: 2022 12 10 7C>, <Slot: 2022 12 13 S>, <Slot: 2022 12 16 MI>, <Slot: 2022 12 20 S>, <Slot: 2022 12 23 S>, <Slot: 2022 09 20 S>, <Slot: 2022 09 22 7C>, <Slot: 2022 09 24 EI>, <Slot: 2022 10 07 7C>, <Slot: 2022 11 19 7C>, <Slot: 2022 10 05 7C>, <Slot: 2022 12 18 EI>, <Slot: 2022 10 15 N>, <Slot: 2022 10 18 S>, '...(remaining elements truncated)...']>

Slot.objects.filter(employee=js, is_terminal=True).count()
30

Slot.objects.filter(employee=js, is_terminal=True).values('streak')
<SlotManager [{'streak': 2}, {'streak': 2}, {'streak': 1}, {'streak': 1}, {'streak': 2}, {'streak': 1}, {'streak': 1}, {'streak': 2}, {'streak': 2}, {'streak': 1}, {'streak': 2}, {'streak': 2}, {'streak': 1}, {'streak': 1}, {'streak': 1}, {'streak': 1}, {'streak': 3}, {'streak': 1}, {'streak': 3}, {'streak': 2}, '...(remaining elements truncated)...']>

list(Slot.objects.filter(employee=js, is_terminal=True).values_list('streak',flat=True))
[2, 2, 1, 1, 2, 1, 1, 2, 2, 1, 2, 2, 1, 1, ...]

sum(list(Slot.objects.filter(employee=js, is_terminal=True).values_list('streak',flat=True)))
49

Slot.objects.filter(employee=js)
<SlotManager [<Slot: 2022 11 15 S>, <Slot: 2022 09 29 S>, <Slot: 2022 09 28 S>, <Slot: 2022 09 26 EP>, <Slot: 2022 10 01 EI>, <Slot: 2022 12 08 S>, <Slot: 2022 12 05 EI>, <Slot: 2022 12 07 S>, <Slot: 2022 12 10 7C>, <Slot: 2022 12 12 S>, <Slot: 2022 12 13 S>, <Slot: 2022 12 15 MI>, <Slot: 2022 12 16 MI>, <Slot: 2022 12 22 S>, <Slot: 2022 12 20 S>, <Slot: 2022 12 23 S>, <Slot: 2022 09 19 S>, <Slot: 2022 09 20 S>, <Slot: 2022 09 22 7C>, <Slot: 2022 09 24 EI>, '...(remaining elements truncated)...']>

Slot.objects.filter(employee=js).count()
48

mm = Employee.objects.get(name="MOLLY")
mm
<Employee: MOLLY>

mm.streak_pref
3

OP = Shift.objects.get(name="OP")
OP
<Shift: OP>

op = OP
op
<Shift: OP>

op.trained_employees()
<EmployeeManager [<Employee: JOSH>, <Employee: BRITTANIE>, <Employee: BRIANNA>, <Employee: ESPERANZA>, <Employee: SABRINA>, <Employee: TRISHA>, <Employee: AMANDA>, <Employee: LINDSAY>, <Employee: LESLIE>]>

op.trained_employees().count()
9

op.trained_employees().count()
9

op.hours
8.0

op.is_iv
True
