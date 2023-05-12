from django.forms.widgets import Input 


class InputGroup (Input) :
    
    input_type    = 'number'
    template_name = 'sch3/input-group.html'
    
    def __init__(self, fieldId, label, icon, attrs=None):
        self.fieldId, self.label, self.icon = fieldId, label, icon
        self.attrs = attrs or {}
    
    def get_context (self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context ['widget']['attrs']['data-field_id'], context ['label'], context ['icon'] = self.fieldId, self.label, self.icon
        return context
    
    