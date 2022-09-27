from django import template
import datetime as dt

register = template.Library()


@register.simple_tag
def secToHours(seconds):
    return seconds.total_seconds() / 3600

#***** BUTTON // GO TO THIS WEEK *****#
@register.inclusion_tag("this_week.html")
def goToThisWeek ():
    today = dt.date.today()
    return {
        'year': today.year,
        'week': today.isocalendar()[1]
    }

#***** BADGE // N DAYS AWAY *****#
@register.inclusion_tag("n_days_away.html")
def nDaysAway (date):
    today = dt.date.today()
    return {
        'n': (date - today).days
    }

@register.inclusion_tag("n_days_away_small.html")
def nDaysAwaySmall (date):
    today = dt.date.today()
    return {
        'n': (date - today).days
    }

    