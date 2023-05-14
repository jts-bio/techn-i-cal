import requests
from django.test import TestCase

from sch.models import *


class TestPublishView(TestCase):

    def setup(self) -> None:
        SD = dt.date(2022, 12, 25)

        Organization.objects.create(name='TestOrg').save()
        Department.objects.create(name='TestDept').save()
        DPT = Department.objects.get(name='TestDept')
        # create 3 instances of a schedule year 2023 number 1 versions A,B,C
        Schedule.objects.create(year=2023, number=1, version='A', start_date=SD, department=DPT).save()
        Schedule.objects.create(year=2023, number=1, version='B', start_date=SD, department=DPT).save()
        Schedule.objects.create(year=2023, number=1, version='C', start_date=SD, department=DPT).save()

        print(Schedule.objects.all())

    def test_publish(self):
        schA = Schedule.objects.get(year=2023, number=1, version='A')  # type: Schedule
        schB = Schedule.objects.get(year=2023, number=1, version='B')
        schC = Schedule.objects.get(year=2023, number=1, version='C')

        schs = Schedule.objects.all()
        build = lambda schMgr: [sch.actions.build_schedule(sch) for sch in schMgr]

        build(schs)
        [s.save() for s in schs]

        self.assertTrue(schA.status == 0)
        self.assertTrue(schB.status == 0)
        self.assertTrue(schC.status == 0)

        print("SLOTCOUNT:", schA.slots.all().count())
        print("SLOTCOUNTOTAL:", Slot.objects.all().count())

        print("DRAFT STATUS QTY:", Schedule.objects.filter(status=0))
        # publish A
        request = requests.Request()
        schA.actions.publish(schA)
        [print(s.status) for s in Schedule.objects.all()]
        schA.save()
        self.assertTrue(schA.status == 1)

        print("PUBLISHED STATUS QTY:", Schedule.objects.filter(status=1))
        print("DISCARDED STATUS QTY:", Schedule.objects.filter(status=2))
