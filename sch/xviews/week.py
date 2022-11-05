from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect, render
from django.db.models import Count
from sch.models import *



def get_days (weekId):
    
    return Workday.objects.filter(date__year=int(weekId[:4]), iweek=int(weekId[6:]))




