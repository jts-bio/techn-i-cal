from django import forms
from .widgets import InputGroup
from .models import *
from django.forms import BaseFormSet, formset_factory, BaseInlineFormSet
import datetime as dt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

TODAY = dt.date.today()


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = '__all__'


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['name', 'start', 'duration', 'occur_days', 'group']
        labels = {
            'name': 'Shift name',
            'start': 'Start time',
            'duration': 'Duration',
            'occur_days': 'Days of the week',
            'employee_class': "Shift for",
            'group': 'Group',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start': forms.TimeInput(attrs={'class': 'form-control'}),
            'duration': forms.TimeInput(attrs={'class': 'form-control'}),
            'occur_days': forms.CheckboxSelectMultiple(attrs={"class": "grid-cols-3"}),
            'group': forms.Select(attrs={"class": "form-control"})
        }


class SSTForm(forms.ModelForm):
    """Form for a single ShiftSlotTemplate, connecting an 
    employee to a shift on a given day"""

    class Meta:
        model = ShiftTemplate
        fields = ['shift', 'sd_id', 'employee']
        labels = {
            'shift': 'Shift',
            'sd_id': 'sD ID',
            'employee': 'Employee',
        }
        widgets = {
            'shift': forms.HiddenInput(),
            'sd_id': forms.HiddenInput(),
            'employee': forms.Select(attrs={
                'class': 'form-control',
            }),
        }


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'name', 'fte', 'department', 'shifts_trained',
            'shifts_available', 'streak_pref',
            'time_pref', 'std_wk_max'
        ]
        labels = {
            'fte': 'FTE',
            'time_pref': 'Shift Time Preference',
            'std_wk_max': 'Standard Weekly Max Hours',
        }
        help_text = dict(
            std_wk_max="The maximum number of hours to scheduling within a week. This should remain at 40hrs for 1FTE employees"
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'shifts_trained': forms.CheckboxSelectMultiple(),
            'shifts_available': forms.CheckboxSelectMultiple(),
            'time_pref': forms.Select(),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shifts_trained'].queryset = Shift.objects.all()
        self.fields['shifts_available'].queryset = Shift.objects.all()
        self.fields['std_wk_max'].initial = 40


    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data


class TechnicianForm(EmployeeForm):
    class Meta(EmployeeForm.Meta):
        model = Employee
        fields = [
            'name',
            'department'
        ]
        widgets = {
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PharmacistForm(EmployeeForm):
    class Meta(EmployeeForm.Meta):
        model = Employee
        fields = [
            'name',
            'fte',
            'initials',
            'time_pref',
        ]
        widgets = {
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EmployeeSelectForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=True)


class EmployeeEditForm(forms.ModelForm):
    shifts_trained = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Shift.objects.all(),
        required=False,
    )
    shifts_available = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Shift.objects.all(),
        required=False,
    )

    time_pref = forms.Select(
        choices=(('AM', 'Morning'), ('PM', 'Evening'), ('XN', 'Overnight'))
    )

    def __init__(self, *args, **kwargs):
        super(EmployeeEditForm, self).__init__(*args, **kwargs)
        dept = self.instance.department
        self.fields['shifts_trained'].queryset = Shift.objects.filter(department=dept)
        self.fields['shifts_available'].queryset = Shift.objects.filter(department=dept)

    class Meta:
        model = Employee
        fields = [
            'name',
            'initials',
            'fte',
            'streak_pref', 'shifts_trained',
            'shifts_available',
            'time_pref', 'hire_date',
            'std_wk_max', 'image_url'
        ]
        labels = {
            'fte': 'FTE',
            'time_pref': "Time Preference",
            'std_wk_max': 'Standard Weekly Max Hours',
            'image_url': 'Profile Image',
        }

        IMAGE_LOOKUP_HYPERSCRIPT = """
            on mutation of @value 
                set link to @value 
                then fetch link then put result into #image_preview
            """

        widgets = {
            'shifts_trained': forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
            'fte': forms.NumberInput(attrs={'class': 'w-28 form-control'}),
            'shifts_available': forms.CheckboxSelectMultiple(attrs={'class': 'grid-cols-3'}),
            'streak_pref': forms.NumberInput(attrs={'class': 'w-28 form-control'}),
            'time_pref': forms.Select(attrs={'class': 'form-control h-10'}),
            'std_wk_max': forms.NumberInput(attrs={'class': 'w-28 form-control'}),
            'image_url': forms.TextInput(attrs={
                'script': IMAGE_LOOKUP_HYPERSCRIPT,
                'class': 'text-xs w-[350px] text-indigo-300 jbm'
            })
        }


class SstEmployeeForm(forms.Form):
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), required=False)
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput(), required=False)
    sd_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(SstEmployeeForm, self).__init__(*args, **kwargs)
        employee = self.initial.get('employee')
        sd_id = self.initial.get('sd_id')

        try:
            trained_shifts = employee.shifts_trained  # type: ignore
        except:
            trained_shifts = Shift.objects.none()
        try:
            wds = 'Sun Mon Tue Wed Thu Fri Sat'.split(" ") * 7
            self.fields['shift'].label = wds[self.initial.get('sd_id')]
        except:
            pass
        if employee:
            other_empls = Employee.objects.exclude(pk=employee.pk)
        else:
            other_empls = Employee.objects.all()
        occupied_ssts = ShiftTemplate.objects.filter(sd_id=self.initial.get('sd_id'), employee__in=other_empls).values(
            'shift')
        sd_id_proxy = self.initial.get('sd_id')
        if sd_id_proxy is None:
            sd_id_proxy = 0
        else:
            sd_id_proxy = int(sd_id_proxy) % 7
        if employee:
            shiftList = employee.shifts_trained.exclude(pk__in=occupied_ssts).filter(occur_days__contains=sd_id_proxy)
        else:
            shiftList = Shift.objects.none()
        if TemplatedDayOff.objects.filter(sd_id=self.initial.get('ppd_id'), employee=employee).exists():
            shiftList = Shift.objects.none()

        self.fields['shift'].choices = list(shiftList.values_list('slug', 'name')) + [("", "-")]  # type: ignore

        if ShiftTemplate.objects.filter(employee=employee, sd_id=self.initial.get('sd_id')).exists():
            self.fields['shift'].initial = ShiftTemplate.objects.get(employee=employee,
                                                                     sd_id=self.initial.get('sd_id')).shift.pk
            # add css class to self.fields['shift'] object

        if TemplatedDayOff.objects.filter(employee=employee, sd_id=sd_id).exists():
            self.fields['shift'].widget.attrs['disabled'] = True
            self.fields['shift'].choices = [(0, "TDO")]

        self.fields['shift'].widget.attrs.update({'class': 'form-control'})


class EmployeeTemplatedDaysOffForm(forms.ModelForm):
    is_templated_off = forms.BooleanField(label='Day off', required=False)
    sd_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput(), required=True)

    class Meta:
        model = TemplatedDayOff
        fields = ['is_templated_off', 'employee', 'sd_id']
        labels = {
            'sd_id': 'Day from month start',
        }
        widgets = {
            'sd_id': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(EmployeeTemplatedDaysOffForm, self).__init__(*args, **kwargs)
        sd_id = self.initial.get('sd_id')
        employee = self.initial.get('employee')
        if sd_id:
            self.fields['is_templated_off'].widget.attrs.update(
                {'class': "Sun Mon Tue Wed Thu Fri Sat".split(" ")[sd_id % 7]})
        if ShiftTemplate.objects.filter(employee=employee, sd_id=sd_id).exists():
            self.fields['is_templated_off'].widget.attrs['disabled'] = True
            self.fields['is_templated_off'].widget.attrs[
                'title'] = "Employee is scheduled for this day. Cannot be templated off until the Shift Template is removed."

    def clean(self):
        cleaned_data = super(EmployeeTemplatedDaysOffForm, self).clean()
        td = TemplatedDayOff.objects.filter(employee=cleaned_data['employee'], sd_id=cleaned_data['sd_id'])
        if cleaned_data['is_templated_off']:  # create or pass
            if td.exists():  # pass
                pass
            else:  # create
                td = TemplatedDayOff.objects.create(employee=cleaned_data['employee'], sd_id=cleaned_data['sd_id'])
                td.save()
        else:  # delete or pass
            if td.exists():  # delete
                td[0].delete()
            else:
                pass


class EmployeeMatchCoworkerTdosForm(forms.ModelForm):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput(), required=True)
    coworker = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.Select(), required=True)

    class Meta:
        model = TemplatedDayOff
        fields = ['employee', 'coworker']

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data


class EmployeeScheduleForm(forms.Form):
    schedule = forms.ModelChoiceField(queryset=Schedule.objects.all())
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput())


class BulkWorkdayForm(forms.Form):
    date_from = forms.DateField(label='From', widget=forms.SelectDateWidget())
    date_to = forms.DateField(label='To', widget=forms.SelectDateWidget())


class SlotForm(forms.ModelForm):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False,
                                      widget=forms.Select(attrs={'class': 'form-control'}))
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), widget=forms.HiddenInput(), to_field_name='name')
    workday = forms.ModelChoiceField(queryset=Workday.objects.all(), widget=forms.HiddenInput(), to_field_name='slug')

    class Meta:
        model = Slot
        fields = ['employee', 'shift', 'workday']

    def __init__(self, *args, **kwargs):
        super(SlotForm, self).__init__(*args, **kwargs)
        self.fields['workday'].initial = self.initial.get('workday')
        self.fields['shift'].initial = self.initial.get('shift')
        self.fields['employee'].initial = self.initial.get('employee')
        shift = self.initial.get('shift')
        workday = self.initial.get('workday')
        slot = Slot.objects.filter(shift=shift, workday=workday, schedule=workday.schedule)
        self.fields['employee'].queryset = Slot.objects.get(workday=workday, shift=shift)._fillableBy()


class SlotForm_OtOveride(forms.ModelForm):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), label='Employee',
                                      widget=forms.Select(attrs={'class': 'form-control'}))
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), label='Shift', widget=forms.HiddenInput(),
                                   to_field_name='name')
    workday = forms.ModelChoiceField(queryset=Workday.objects.all(), label='Workday', widget=forms.HiddenInput(),
                                     to_field_name='slug')

    class Meta:
        model = Slot
        fields = ['employee', 'shift', 'workday']

    def __init__(self, *args, **kwargs):
        super(SlotForm_OtOveride, self).__init__(*args, **kwargs)
        shift = Shift.objects.get(name=self.initial['shift'])
        workday = Workday.objects.get(slug=self.initial['workday'])
        self.fields['employee'].queryset = Slot.objects.get(workday=workday, shift=shift).fillableBy()
        self.fields['employee'].label = shift.name


class ClearWeekSlotsForm(forms.Form):
    confirm = forms.BooleanField(label='Confirm', required=True)

    class Meta:
        fields = ['confirm']
        widgets = {'confirm': forms.CheckboxInput(attrs={'class': 'form-control'})}


class SstForm(forms.Form):
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), widget=forms.HiddenInput())
    sd_id = forms.IntegerField(widget=forms.HiddenInput())
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False,
                                      widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(SstForm, self).__init__(*args, **kwargs)  # init the form
        # Select options set as form renders
        shift = self.initial.get('shift')
        trained_emps = Employee.objects.filter(shifts_trained__name=shift)
        conflicting_tmpl = ShiftTemplate.objects.filter(sd_id=self.initial.get('sd_id')).exclude(shift=shift).values(
            'employee')

        emp_choices = trained_emps.exclude(pk__in=conflicting_tmpl)
        tdos = TemplatedDayOff.objects.filter(sd_id=self.initial.get('sd_id')).values('employee')
        emp_choices = emp_choices.exclude(pk__in=tdos)
        if self.initial.get('sd_id'):
            if str(self.initial.get('sd_id') % 7) in list(shift.occur_days):
                self.fields['employee'].choices = list(emp_choices.values_list('id', 'name')) + [
                    ("", "---------------")]
        else:
            self.fields['employee'].choices = [("", "---------------")]

        if ShiftTemplate.objects.filter(
                shift=shift,
                sd_id=self.initial.get('sd_id')).exists():
            self.fields['employee'].initial = ShiftTemplate.objects.get(
                shift=shift,
                sd_id=self.initial.get('sd_id')).employee

        # custom labels 
        wds = 'Sun Mon Tue Wed Thu Fri Sat'.split(" ")
        try:
            self.fields['employee'].label = wds[int(self.initial.get('ppd_id')) % 7]  # type: ignore
        except:
            pass


SHIFT_UNIQUE_MESG = "Shifts must be unique."


class SstFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        # check that all shifts are unique
        shifts = []
        for form in self.forms:
            shift = form.cleaned_data['shift']
            if shift in shifts:
                raise forms.ValidationError(SHIFT_UNIQUE_MESG)
            shifts.append(shift)


class PTOForm(forms.ModelForm):
    class Meta:
        model = PtoRequest
        fields = ['employee', 'workday']
        widgets = {
            'employee': forms.HiddenInput(),
            'workday': forms.DateField(widget=forms.SelectDateWidget()),
        }


class PTODayForm(forms.ModelForm):
    class Meta:
        model = PtoRequest
        fields = ['employee', 'workday']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'workday': forms.HiddenInput()
        }


class PTORangeForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.HiddenInput())
    date_from = forms.DateField(label='From', widget=forms.SelectDateWidget())
    date_to = forms.DateField(label='To', widget=forms.SelectDateWidget())

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


class SlotPriorityForm(forms.ModelForm):
    class Meta:
        model = SlotPriority
        fields = ['iweekday', 'shift', 'priority']
        widgets = {
            'employee': forms.HiddenInput(),
            'shift': forms.HiddenInput(),
        }


class SlotPriorityFormSet(BaseFormSet):

    def clean(self):
        if any(self.errors):
            return
        # check that all shift-wd pairs are unique
        pairs = []
        for form in self.forms:
            shift = form.cleaned_data['shift']
            iweekday = form.cleaned_data['iweekday']
            if (shift, iweekday) in pairs:
                raise forms.ValidationError(SHIFT_UNIQUE_MESG)
            pairs.append((shift, iweekday))

    def save(self, commit=True):
        for form in self.forms:
            form.save(commit=commit)


class PtoResolveForm(forms.Form):
    slot = forms.ModelChoiceField(queryset=Slot.objects.all(), widget=forms.HiddenInput())
    pto_req = forms.ModelChoiceField(queryset=PtoRequest.objects.all(), widget=forms.HiddenInput())
    action = forms.ChoiceField(choices=[
        ('es', 'Empty Slot'), ('rp', 'Reject PTO Request')
    ], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        super(PtoResolveForm, self).__init__(*args, **kwargs)
        self.fields['slot'].initial = self.initial.get('slot')
        self.fields['pto_req'].initial = self.initial.get('pto_req')
        self.fields['action'].initial = 'rp'

    def clean(self):
        cleaned_data = super(PtoResolveForm, self).clean()
        slot = cleaned_data.get('slot')
        pto_req = cleaned_data.get('ptoreq')


PREF_SCORES = (
    ('SP', 'Strongly Prefer'),
    ('P', 'Prefer'),
    ('N', 'Neutral'),
    ('D', 'Dislike'),
    ('SD', 'Strongly Dislike'),
)


class EmployeeShiftPreferencesForm(forms.ModelForm):
    class Meta:
        model = ShiftPreference
        fields = ['employee', 'shift', 'priority']
        widgets = {
            'employee': forms.HiddenInput(),
            'shift': forms.HiddenInput(),
            'priority': forms.Select(choices=PREF_SCORES, attrs={'onchange': 'updateColor(this)'})
        }

        labels = {
            'priority': 'Preference'
        }

        def clean(self):
            cleaned_data = super(EmployeeShiftPreferencesForm, self).clean()
            employee_id = cleaned_data.get('employee_id')
            shift = cleaned_data.get('shift')


class EmployeeShiftPreferencesFormset(BaseInlineFormSet):

    def clean(self):
        if any(self.errors):
            return
        # check that all shifts are unique
        shifts = []
        for form in self.forms:
            shift = form.cleaned_data['shift']
            if shift in shifts:
                raise forms.ValidationError(SHIFT_UNIQUE_MESG)
            shifts.append(shift)

    def save(self, commit=True):
        for form in self.forms:
            form.save(commit=commit)


class TrainedEmployeeShiftForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.HiddenInput())
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.all(),
        widget=forms.HiddenInput())
    is_trained = forms.BooleanField(
        required=False)
    is_available = forms.BooleanField(
        required=False)

    def __init__(self, *args, **kwargs):
        super(TrainedEmployeeShiftForm, self).__init__(*args, **kwargs)
        self.fields['is_trained'].label = 'Trained'
        self.fields['is_available'].label = 'Available'


class EmployeeCoworkerSelectForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.Select())


START_DATE_SET = [(Schedule.START_DATES[2023][i], Schedule.START_DATES[2023][i]) for i in
                  range(0, len(Schedule.START_DATES[2023]))]



class ShiftAvailableEmployeesForm(forms.Form):
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), widget=forms.HiddenInput())
    employees = forms.ModelMultipleChoiceField(queryset=Employee.objects.all(), widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super(ShiftAvailableEmployeesForm, self).__init__(*args, **kwargs)
        self.fields['shift'].label = ''
        self.fields['employees'].label = ''
