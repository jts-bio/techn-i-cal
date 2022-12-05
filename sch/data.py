

from .models import *
from datetime import time

Shift.objects.create(name="MI", start_time=time=(9, 0), end_time=time=(17, 0))
User.objects.create (name="Josh", cls="CPhT", fte_14_hr=50, )