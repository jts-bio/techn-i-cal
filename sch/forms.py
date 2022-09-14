from django import forms
from .models import Slot, Workday, Shift, Employee, ShiftTemplate
from django.forms import BaseFormSet, formset_factory


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

    def clean(self):
        cleaned_data = super(SlotForm, self).clean()
        employee = cleaned_data.get('employee')
        workday  = cleaned_data.get('workday')
        shift    = cleaned_data.get('shift')
        return cleaned_data



class TemplateSlotForm (forms.Form):
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), widget=forms.HiddenInput())
    ppd_id = forms.IntegerField(widget=forms.HiddenInput())
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-control'}))

    def __init__(self, *args, **kwargs):
        super(TemplateSlotForm, self).__init__(*args, **kwargs) #init the form
        # Select options set as form renders
        shift                            = self.initial.get('shift')
        self.fields['employee'].choices  = list(Employee.objects.filter(shifts_trained__name=shift).values_list('id','name')) + [("","---------")]
        if ShiftTemplate.objects.filter(shift=shift, ppd_id=self.initial.get('ppd_id')).exists():
            self.fields['employee'].initial = ShiftTemplate.objects.get(shift=shift, ppd_id=self.initial.get('ppd_id')).employee.id
        
        # custom labels 
        wds = 'Sun-A Mon-A Tue-A Wed-A Thu-A Fri-A Sat-A Sun-B Mon-B Tue-B Wed-B Thu-B Fri-B Sat-B'.split(" ")
        try:
            self.fields['employee'].label    = wds[int(self.initial.get('ppd_id'))]
        except:
            pass
        print(self.initial.get('employee'))



class TssFormSet (BaseFormSet):
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



from django import forms
from .models import Slot, Workday, Shift, Employee, ShiftTemplate
from django.forms import BaseFormSet, formset_factory



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

    def clean(self):
        cleaned_data = super(SlotForm, self).clean()
        employee = cleaned_data.get('employee')
        workday  = cleaned_data.get('workday')
        shift    = cleaned_data.get('shift')
        return cleaned_data
        


class TemplateSlotForm (forms.Form):
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), widget=forms.HiddenInput())
    ppd_id = forms.IntegerField(widget=forms.HiddenInput())
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-control'}))



    def __init__(self, *args, **kwargs):
        super(TemplateSlotForm, self).__init__(*args, **kwargs) #init the form
        # Select options set as form renders
        shift                            = self.initial.get('shift')
        self.fields['employee'].choices  = list(Employee.objects.filter(shifts_trained__name=shift).values_list('id','name')) + [("","---------")]
        if ShiftTemplate.objects.filter(shift=shift, ppd_id=self.initial.get('ppd_id')).exists():
            self.fields['employee'].initial = ShiftTemplate.objects.get(shift=shift, ppd_id=self.initial.get('ppd_id')).employee.id
        
        # custom labels 
        wds = 'Sun-A Mon-A Tue-A Wed-A Thu-A Fri-A Sat-A Sun-B Mon-B Tue-B Wed-B Thu-B Fri-B Sat-B'.split(" ")
        try:
            self.fields['employee'].label    = wds[int(self.initial.get('ppd_id'))]
        except:
            pass
        print(self.initial.get('employee'))



class TssFormSet (BaseFormSet):
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



