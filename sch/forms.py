from django import forms
from .models import PtoRequest, Slot, Workday, Shift, Employee, ShiftTemplate
from django.forms import BaseFormSet, formset_factory
import datetime as dt

TODAY = dt.date.today()


class ShiftForm (forms.ModelForm) :
    class Meta:
        model = Shift
        fields = ['name', 'start', 'duration','occur_days']
        labels = {
            'name': 'Shift name',
            'start': 'Start time',
            'duration': 'Duration',
            'occur_days': 'Days of the week',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start': forms.TimeInput(attrs={'class': 'form-control'}),
            'duration': forms.TimeInput(attrs={'class': 'form-control'}),
            'occur_days': forms.CheckboxSelectMultiple(),
        }


class SSTForm (forms.ModelForm) :
    class Meta:
        model = ShiftTemplate
        fields = ['shift', 'ppd_id', 'employee']
        labels = {
            'shift': 'Shift',
            'ppd_id': 'PPD ID',
            'employee': 'Employee',
        }
        widgets = {
            'shift': forms.HiddenInput(),
            'ppd_id' : forms.HiddenInput(),
            'employee': forms.Select(attrs={'class': 'form-control'}),
        }

class EmployeeForm (forms.ModelForm) :
    class Meta:
        model = Employee
        fields = ['name', 'fte_14_day', 'shifts_trained', 'shifts_available', 'streak_pref']
        labels = {
            'fte_14_day': 'FTE (hrs/ 14 days)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'shifts_trained': forms.CheckboxSelectMultiple(),
            'shifts_available': forms.CheckboxSelectMultiple(),
        }

class EmployeeEditForm (forms.ModelForm) :
    class Meta:
        model = Employee
        fields = ['fte_14_day', 'streak_pref', 'shifts_trained', 'shifts_available']
        labels = {
            'fte_14_day': 'FTE (hours per 14 days)',
        }
        widgets = {
            'shifts_trained': forms.CheckboxSelectMultiple(),
            'shifts_available': forms.CheckboxSelectMultiple(),
            'streak_pref': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class BulkWorkdayForm (forms.Form) :
    
    date_from = forms.DateField(label='From', widget=forms.SelectDateWidget())
    date_to   = forms.DateField(label='To', widget=forms.SelectDateWidget())

class SlotForm (forms.ModelForm):

    employee    = forms.ModelChoiceField(queryset=Employee.objects.all(), label='Employee', widget=forms.Select(attrs={'class': 'form-control'}))
    shift       = forms.ModelChoiceField(queryset=Shift.objects.all(), label='Shift', widget=forms.HiddenInput(), to_field_name='name')
    workday     = forms.ModelChoiceField(queryset=Workday.objects.all(), label='Workday', widget=forms.HiddenInput(), to_field_name='slug')

    class Meta:
        model = Slot
        fields = ['employee', 'shift', 'workday']
        
    def __init__(self, *args, **kwargs):
        super(SlotForm, self).__init__(*args, **kwargs)
        shift = Shift.objects.get(name=self.initial['shift'])
        workday = Workday.objects.get(slug=self.initial['workday'])
        self.fields['employee'].queryset = Employee.objects.can_fill_shift_on_day(shift=shift, workday=workday)






class SstEmployeeForm (forms.Form):
    
    shift    = forms.ModelChoiceField(queryset=Shift.objects.all(), required=False)
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput())
    ppd_id   = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(SstEmployeeForm, self).__init__(*args, **kwargs)

        employee = self.initial.get('employee')
        try:
            trained_shifts = employee.shifts_trained # type: ignore
        except:
            trained_shifts = Shift.objects.none()

        try:
            wds = 'Sun-A Mon-A Tue-A Wed-A Thu-A Fri-A Sat-A Sun-B Mon-B Tue-B Wed-B Thu-B Fri-B Sat-B'.split(" ")
            self.fields['shift'].label = wds[self.initial.get('ppd_id')]
        except:
            pass
        if employee:
            other_empls = Employee.objects.exclude(pk=employee.pk)
        else:
            other_empls = Employee.objects.all()
        occupied_ssts = ShiftTemplate.objects.filter(ppd_id=self.initial.get('ppd_id'),employee__in=other_empls).values('shift')
        ppd_id_proxy = self.initial.get('ppd_id')
        if ppd_id_proxy is None:
            ppd_id_proxy = 0
        if ppd_id_proxy > 6:
            ppd_id_proxy -= 7
        if employee:
            shiftList = employee.shifts_trained.exclude(id__in=occupied_ssts).filter(occur_days__contains=ppd_id_proxy)
        else:
            shiftList = Shift.objects.none()

        self.fields['shift'].choices = list(shiftList.values_list('id', 'name')) + [("","---------")]# type: ignore

        if ShiftTemplate.objects.filter(employee=employee, ppd_id=self.initial.get('ppd_id')).exists():
            self.fields['shift'].initial = ShiftTemplate.objects.get(employee=employee, ppd_id=self.initial.get('ppd_id')).shift.id
        


class SstForm (forms.Form):
    shift    = forms.ModelChoiceField(queryset=Shift.objects.all(), widget=forms.HiddenInput())
    ppd_id   = forms.IntegerField(widget=forms.HiddenInput())
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-control'}))

    def __init__(self, *args, **kwargs):
        super(SstForm, self).__init__(*args, **kwargs) #init the form
        # Select options set as form renders
        shift  = self.initial.get('shift')
        trained_emps = Employee.objects.filter(shifts_trained__name=shift)
        conflicting_tmpl = ShiftTemplate.objects.filter(ppd_id=self.initial.get('ppd_id')).exclude(shift=shift).values('employee')
        emp_choices = trained_emps.exclude(pk__in=conflicting_tmpl)
        self.fields['employee'].choices  = list(emp_choices.values_list('id','name')) + [("","---------")] # type: ignore
        if ShiftTemplate.objects.filter(
                    shift=shift, 
                    ppd_id=self.initial.get('ppd_id')).exists():
            self.fields['employee'].initial = ShiftTemplate.objects.get(
                        shift=shift, 
                        ppd_id=self.initial.get('ppd_id')).employee
        
        # custom labels 
        wds = 'Sun-A Mon-A Tue-A Wed-A Thu-A Fri-A Sat-A Sun-B Mon-B Tue-B Wed-B Thu-B Fri-B Sat-B'.split(" ")
        try:
            self.fields['employee'].label    = wds[int(self.initial.get('ppd_id'))] # type: ignore
        except:
            pass



class SstFormSet (BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        # check that all shifts are unique
        shifts = []
        for form in self.forms:
            shift = form.cleaned_data['shift']
            if shift in shifts:
                raise forms.ValidationError("Shifts must be unique.")
            shifts.append(shift)


class PTOForm (forms.ModelForm) :
    class Meta:
        model = PtoRequest
        fields = ['employee', 'workday']
        widgets = {
            'employee': forms.HiddenInput(),
            'workday': forms.DateField(widget=forms.SelectDateWidget()),
        }

class PTORangeForm (forms.Form) :

    employee  = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput())
    date_from = forms.DateField(label='From', widget=forms.SelectDateWidget())
    date_to   = forms.DateField(label='To', widget=forms.SelectDateWidget())

    def __init__(self, *args, **kwargs):
        super(PTORangeForm, self).__init__(*args, **kwargs)
        self.fields['employee'].initial = self.initial.get('employee')
        self.fields['date_from'].initial = TODAY + dt.timedelta(days=30)
        self.fields['date_to'].initial = TODAY + dt.timedelta(days=32)

    def clean(self):
        cleaned_data = super(PTORangeForm, self).clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Date from must be before date to.")
    
        


    