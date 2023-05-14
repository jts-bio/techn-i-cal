from django.urls import path, include
from . import views


app_name = 'dept'

urlpatterns = [

        path('<org>/<dept>/', views.dept_detail, name='dept-detail'),
        path('<org>/<dept>/new-employee/', views.new_employee_partial, name='new-employee-partial'),

    ]