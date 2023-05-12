from django import forms
from sch.models import Schedule, Department


class GenerateNewScheduleForm(forms.Form):
    start_date = forms.ChoiceField(
        label="Start Date"
    )

    department = forms.ModelChoiceField(queryset=Department.objects.none(), widget=forms.Select())

    def __init__(self, user, *args, **kwargs):
        super(GenerateNewScheduleForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['start_date'].choices = user.employee.department.org.start_dates()
            self.fields['department'].queryset = Department.objects.filter(org=user.employee.department.org)