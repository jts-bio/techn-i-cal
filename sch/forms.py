from django import forms
from .models import Slot, Workday, Shift, Employee, ShiftTemplate
from django.forms import BaseFormSet, formset_factory



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
            'fte_14_day': 'FTE (hours per 14 days)',
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
    date_to = forms.DateField(label='To', widget=forms.SelectDateWidget())

class SlotForm (forms.Form):

    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False)
    workday = forms.HiddenInput()
    shift   = forms.HiddenInput()

    def __init__(self, *args, **kwargs):
        super(SlotForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.pk:
            self.fields['employee'].initial = instance.employee
            self.fields['employee'].widget.attrs['readonly'] = True

            self.fields['workday'].initial  = instance.workday
            self.fields['workday'].widget.attrs['readonly'] = True

            self.fields['shift'].initial    = instance.shift


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
        occupied_ssts = ShiftTemplate.objects.filter(ppd_id=self.initial.get('ppd_id')).values('shift').exclude(employee=employee)
        shiftList = trained_shifts.exclude(pk__in=occupied_ssts)
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




