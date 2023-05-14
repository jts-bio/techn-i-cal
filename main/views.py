from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *

# Create your views here.

class ScheduleViews:

   @login_required
   def dept_schedules_list(request):
      profile = Profile.objects.get(user=request.user)
      organization = profile.organization
      
      if request.method == "POST":
         start_date_data   = request.POST.get('start_date')
         start_date        = dt.datetime.strptime(start_date_data, '%Y-%m-%d').date()

         year            = start_date.year
         department      = organization.departments.filter(pk=request.POST.get('department')).first()

         schedule_number = list(filter(lambda x: x.year == year, department.schedule_start_dates)).index(start_date) + 1
               
         Schedule.objects.create(
                     start_date=start_date,
                     year=year,
                     number=schedule_number,
                     slug=f"{year}-S{schedule_number}",
                     published=False,
                     department=department
               )

      return render(request, 'pages/schedules/list.pug', {
         'organization':organization, 
         'today':timezone.now().date(), 
         "years":Schedule.objects.filter(department__organization=organization).values('year').distinct()
         } )
   
   def sch_detail(request,dept,yr,n):
      department = Department.objects.get(slug=dept)
      schedule = Schedule.objects.get(year=yr, number=n, department=department)
      schedule.save()

      if request.method == "POST":
         version = schedule.versions.count() + 1
         Version.objects.create(
            schedule=schedule,
            name= f"{version}",
            percent=0,
            created_by=Profile.objects.get(user=request.user)
            )

      return render(request, 'pages/schedules/detail.pug', {'schedule':schedule} )
   
   
   class ScheduleUtils:
      def pto_cal(request,dept,year,n,empl):
         department = Department.objects.get(slug=dept)
         schedule = Schedule.objects.get(year=year, number=n, department=department)
         employee = Employee.objects.get(pk=empl)
         weeks = [schedule.start_date + dt.timedelta(days=7*i) for i in range(schedule.department.schedule_week_count)]
         return render(request, 'pages/schedules/pto-sch.pug', {'schedule':schedule, 'employee':employee} )

class VersionViews:

   def ver_detail (request,dept,yr,n,v):
      department = Department.objects.get(slug=dept)
      schedule = Schedule.objects.get(year=yr, number=n, department=department)
      version = Version.objects.get(schedule=schedule, name=v)
      version.save()
      return render(request, 'pages/versions/detail.pug', {'version':version} )

   def ver_solve (request,dept,yr,n,v):
      department = Department.objects.get(slug=dept)
      schedule = Schedule.objects.get(year=yr, number=n, department=department)
      version = Version.objects.get(schedule=schedule, name=v)
      n = 0
      for slot in Slot.objects.filter(workday__version=version, employee__isnull=True).order_by('?'):
         if slot.fills_with().count() > 0:
            slot.employee = slot.fills_with().first()
            slot.save()
            n += 1
      
      return HttpResponse(f"Filled {n} slots")
   
   def ver_clear (request,dept,yr,n,v):
      department = Department.objects.get(slug=dept)
      schedule = Schedule.objects.get(year=yr, number=n, department=department)
      version = Version.objects.get(schedule=schedule, name=v)
      n = 0
      for slot in Slot.objects.filter(workday__version=version, employee__isnull=False):
         slot.employee = None
         slot.save()
         n += 1
      
      return HttpResponse(f"Cleared {n} slots")

   def ver_delete (request,dept,yr,n,v):
      if request.user.profile.admin:
         department = Department.objects.get(slug=dept)
         schedule = Schedule.objects.get(year=yr, number=n, department=department)
         version = Version.objects.get(schedule=schedule, name=v)
         version.delete()
         return HttpResponse(f"Deleted {version}")
      else:
         return HttpResponse("You are not authorized to delete this version")
      
   

class WorkdayViews:
   pass

class SlotViews:
   def slot_detail(request,dept,yr,n,v,wd,s):
      department = Department.objects.get(slug=dept)
      schedule = Schedule.objects.get(year=yr, number=n, department=department)
      version = Version.objects.get(schedule=schedule, name=v)
      workday = Workday.objects.get(version=version, date=wd)
      slot = Slot.objects.get(workday=workday, shift=s)

      if request.method == "POST":
         fillingwith = request.POST.get('employee')
         slot.employee = Employee.objects.get(pk=fillingwith)
         slot.save()
         return HttpResponse(f"Filled {slot} with {slot.employee}")
         
      return render(request, 'pages/slots/detail.pug', {'slot':slot} )

class EmployeeViews:
   def shift_pref_view(request,pk):
      employee = Employee.objects.get(pk=pk)
      if request.method == "POST":
         employee.shift_prefs.all().delete()
         i = 0
         sp = request.POST.get('4')
         if sp:
            for s in sp:
               i += 1
               employee.shift_prefs.add(Shift.objects.get(slug=s), rank=i, qual=4)
            p = request.POST.get('3')
         if p:
            for s in p:
               i += 1
               employee.shift_prefs.add(Shift.objects.get(slug=s), rank=i, qual=3)
            n = request.POST.get('2')
         if n:
            for s in n:
               i += 1
               employee.shift_prefs.add(Shift.objects.get(slug=s), rank=i, qual=2)
            d = request.POST.get('1')
         if p:
            for s in d:
               i += 1
               employee.shift_prefs.add(Shift.objects.get(slug=s), rank=i, qual=1)
            sd = request.POST.get('0')
         if sp:
            for s in sd:
               i += 1
               employee.shift_prefs.add(Shift.objects.get(slug=s), rank=i, qual=0)

      return render(request, 'pages/employees/shift-pref.pug', {'employee':employee} )

   def emp_list(request):
      user = request.user
      empls = user.profile.organization.employees.all()
      depts = Department.objects.filter(organization=user.profile.organization)
      return render(request, 'pages/employees/list.pug', {'employees':empls,"depts": depts} )
   