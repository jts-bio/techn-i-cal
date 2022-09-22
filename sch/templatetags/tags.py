from django import template
import datetime as dt

register = template.Library()





@register.simple_tag
def secToHours(seconds):
    return seconds.total_seconds() / 3600

@register.inclusion_tag("this_week.html")
def goToThisWeek ():
    today = dt.date.today()
    return {
        'year': today.year,
        'week': today.isocalendar()[1]
    }