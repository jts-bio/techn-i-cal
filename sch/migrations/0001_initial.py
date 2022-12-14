# Generated by Django 4.1.1 on 2022-12-05 14:38

import computedfields.resolver
import datetime
from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('fte_14_day', models.FloatField(default=80)),
                ('fte', models.FloatField(default=1)),
                ('streak_pref', models.IntegerField(default=3)),
                ('trade_one_offs', models.BooleanField(default=True)),
                ('cls', models.CharField(blank=True, choices=[('CPhT', 'CPhT'), ('RPh', 'RPh')], default='CPhT', max_length=20, null=True)),
                ('evening_pref', models.BooleanField(default=False)),
                ('slug', models.CharField(blank=True, max_length=25, primary_key=True, serialize=False)),
                ('hire_date', models.DateField(default=datetime.date(2018, 4, 11))),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeClass',
            fields=[
                ('id', models.CharField(max_length=5, primary_key=True, serialize=False)),
                ('class_name', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('number', models.IntegerField()),
                ('start_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(default=None, null=True)),
                ('number', models.IntegerField(default=None, null=True)),
                ('start_date', models.DateField()),
                ('status', models.IntegerField(choices=[(0, 'w'), (1, 'o'), (2, 'r'), (3, 'k'), (4, 'i'), (5, 'n'), (6, 'g'), (7, ','), (8, 'f'), (9, 'i'), (10, 'n'), (11, 'i'), (12, 's'), (13, 'h'), (14, 'e'), (15, 'd'), (16, ','), (17, 'd'), (18, 'i'), (19, 's'), (20, 'c'), (21, 'a'), (22, 'r'), (23, 'd'), (24, 'e'), (25, 'd')], default=0)),
                ('version', models.CharField(default='A', max_length=1)),
                ('slug', models.CharField(default='', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('cls', models.CharField(choices=[('CPhT', 'CPhT'), ('RPh', 'RPh')], max_length=20, null=True)),
                ('start', models.TimeField()),
                ('duration', models.DurationField()),
                ('hours', models.FloatField()),
                ('group', models.CharField(choices=[('AM', 'AM'), ('MD', 'MD'), ('PM', 'PM'), ('XN', 'XN')], max_length=10, null=True)),
                ('occur_days', multiselectfield.db.fields.MultiSelectField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')], default=[0, 1, 2, 3, 4, 5, 6], max_length=14)),
                ('is_iv', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iweek', models.IntegerField(blank=True, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('number', models.IntegerField(blank=True, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('period', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='weeks', to='sch.period')),
                ('schedule', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='weeks', to='sch.schedule')),
            ],
        ),
        migrations.CreateModel(
            name='Workday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('slug', models.CharField(blank=True, max_length=30, null=True)),
                ('iweekday', models.IntegerField(default=-1)),
                ('iweek', models.IntegerField(default=-1)),
                ('iperiod', models.IntegerField(default=-1)),
                ('ischedule', models.IntegerField(default=-1)),
                ('ppd_id', models.IntegerField(default=-1)),
                ('sd_id', models.IntegerField(default=-1)),
                ('period', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workdays', to='sch.period')),
                ('schedule', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workdays', to='sch.schedule')),
                ('week', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workdays', to='sch.week')),
            ],
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('empl_sentiment', models.SmallIntegerField(default=None, null=True)),
                ('is_turnaround', models.BooleanField(default=False)),
                ('is_terminal', models.BooleanField(default=False)),
                ('streak', models.SmallIntegerField(default=None, null=True)),
                ('employee', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='sch.employee')),
                ('period', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='sch.period')),
                ('schedule', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='sch.schedule')),
                ('shift', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='sch.shift')),
                ('week', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='sch.week')),
                ('workday', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='sch.workday')),
            ],
        ),
        migrations.CreateModel(
            name='ShiftTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sd_id', models.IntegerField()),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sch.employee')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sch.shift')),
            ],
        ),
        migrations.CreateModel(
            name='ShiftPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.CharField(choices=[('SP', 'Strongly Prefer'), ('P', 'Prefer'), ('N', 'Neutral'), ('D', 'Dislike'), ('SD', 'Strongly Dislike')], default='N', max_length=2)),
                ('score', models.IntegerField(editable=False)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sch.employee')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sch.shift')),
            ],
            bases=(computedfields.resolver._ComputedFieldsModelBase, models.Model),
        ),
        migrations.CreateModel(
            name='SchedulingMax',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('pay_period', models.IntegerField(blank=True, null=True)),
                ('max_hours', models.IntegerField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sch.employee')),
            ],
        ),
        migrations.CreateModel(
            name='PtoRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('workday', models.DateField(blank=True, null=True)),
                ('dateCreated', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('P', 'Pending'), ('A', 'Approved'), ('D', 'Denied')], default='P', max_length=20)),
                ('manager_approval', models.BooleanField(default=False)),
                ('sd_id', models.IntegerField(default=-1)),
                ('stands_respected', models.BooleanField(editable=False)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sch.employee')),
            ],
            options={
                'abstract': False,
            },
            bases=(computedfields.resolver._ComputedFieldsModelBase, models.Model),
        ),
        migrations.AddField(
            model_name='period',
            name='schedule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='sch.schedule'),
        ),
        migrations.AddField(
            model_name='employee',
            name='shifts_available',
            field=models.ManyToManyField(related_name='available', to='sch.shift'),
        ),
        migrations.AddField(
            model_name='employee',
            name='shifts_trained',
            field=models.ManyToManyField(related_name='trained', to='sch.shift'),
        ),
        migrations.CreateModel(
            name='TemplatedDayOff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sd_id', models.IntegerField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tdos', to='sch.employee')),
            ],
            options={
                'unique_together': {('employee', 'sd_id')},
            },
        ),
        migrations.CreateModel(
            name='SlotPriority',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iweekday', models.IntegerField()),
                ('priority', models.CharField(choices=[('L', 'Low'), ('M', 'Medium'), ('H', 'High'), ('U', 'Urgent')], default='M', max_length=20)),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sch.shift')),
            ],
            options={
                'unique_together': {('iweekday', 'shift')},
            },
        ),
        migrations.AddConstraint(
            model_name='slot',
            constraint=models.UniqueConstraint(fields=('workday', 'shift'), name='Shift Duplicates on day'),
        ),
        migrations.AddConstraint(
            model_name='slot',
            constraint=models.UniqueConstraint(fields=('workday', 'employee'), name='Employee Duplicates on day'),
        ),
        migrations.AlterUniqueTogether(
            name='shifttemplate',
            unique_together={('shift', 'sd_id')},
        ),
        migrations.AlterUniqueTogether(
            name='shiftpreference',
            unique_together={('employee', 'shift')},
        ),
        migrations.AlterUniqueTogether(
            name='schedulingmax',
            unique_together={('employee', 'year', 'pay_period')},
        ),
    ]
