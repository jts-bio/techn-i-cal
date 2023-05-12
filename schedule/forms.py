from django import forms

from sch.models import Department

from django.forms import BaseFormSet, formset_factory, BaseInlineFormSet
import datetime as dt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User






class GenerateNewScheduleForm (forms.Form):
    
    start_date = forms.ChoiceField(
                           label="Start Date"
                        )
    department = forms.ModelChoiceField(
                           queryset=Department.objects.all(), 
                           widget=forms.Select(),
                           label="DEPT"
                        )
    
    def __init__(self, *args, **kwargs):
       # get request.user
       user = kwargs.pop('user')
       super(GenerateNewScheduleForm, self).__init__(*args, **kwargs)
       self.fields['department'].queryset = Department.objects.filter(organization=user.organization)
       self.fields['start_date'].queryset = Organization.objects.get(pk=user.organization.pk)
