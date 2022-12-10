from django.forms import modelformset_factory , widgets
from .models import TemplatedDayOff, PtoRequest

EmployeeTDOFormset = modelformset_factory(
    TemplatedDayOff,fields=('employee','sd_id'),
    widgets= {
        'employee': widgets.HiddenInput(),
        'sd_id': widgets.CheckboxInput(),
    } 
    )

