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
    
    

@register.inclusion_tag("LeftArrow.svg")
def backArrow (width="20px", height="20px", fill="#e1e1e1",fillB="#acffde"):
    return {'width': width,'height': height,'fill': fill, 'fillB': fillB}

@register.inclusion_tag("RightArrow.svg")
def forwardArrow (width="20px", height="20px", fill="#e1e1e1",fillB="#acffde"):
    return {'width': width,'height': height,'fill': fill, 'fillB': fillB}

@register.inclusion_tag("Lock.svg")
def lockIcon (width="20px", height="20px", fill="#e1e1e1"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("SupportStaff.svg")
def fillTemplateIcon (width="40px", height="40px", fill="#e1e1e1"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("FlowRate Logo.svg")
def logoIcon (width="90px", height="90px"):
    return {'width': width,'height': height}

@register.inclusion_tag("AddNew.svg")
def addNewIcon (width="20px", height="20px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("AddPerson.svg")
def newEmployee (width="20px", height="20px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("Add.svg")
def plusIcon (width="20px", height="20px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("Solve.svg")
def solveIcon (width="30px", height="30px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("Clear.svg")
def clearIcon (width="30px", height="30px", fill="#eebbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("Edit.svg")
def editIcon (width="20px", height="20px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("Robot.svg")
def robotIcon (width="30px", height="30px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("Syringe.svg")
def syringeIcon (width="30px", height="30px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("Date.svg")
def dateIcon (width="30px", height="30px", fill="#bbbbbb"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("favorite.svg")
def favoriteIcon (width="20px", height="20px", fill="#bbbbffaa"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("vacation.svg")
def vacationIcon (width="20px", height="20px", fill="#ffbbbb88"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("shuffle.svg")
def shuffleIcon (width="20px", height="20px", fill="#ff77eeaa"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("sortingHat.svg")
def sortingHatIcon (width="20px", height="20px", fill="#bbbbbbaa"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("posion.svg")
def posionIcon (width="20px", height="20px", fill="#003322dd"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("mortarPestle.svg")
def mortarIcon (width="20px", height="20px", fill="#8899dddd"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("RxStaff.svg")
def staffIcon (width="20px", height="20px", fill="#8899dddd"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("moon.svg")
def moonIcon (width="20px", height="20px", fill="indigo"):
    return {'width': width,'height': height,'fill': fill}


@register.simple_tag
def todayYear ():
    return dt.date.today().year 

@register.simple_tag
def todaySch ():
    return 7

@register.inclusion_tag('iconCard.html')
def iconCard (title="", body="", cardUrl="", badge=""):
    return {'title':title, 'body':body, 'cardUrl':cardUrl, 'badge':badge} 

@register.inclusion_tag('iconCard_listBody.html')
def iconCard2 (title="", body=[], cardUrl="", badge=""):
    return {'title':title, 'body':body, 'cardUrl':cardUrl, 'badge':badge}

@register.inclusion_tag('figCard.html')
def figCard (title="", figure="",unit="",percComplete="", tot=""):
    return {'title':title, 'figure': figure, 'unit':unit, 'percComplete':percComplete, 'tot':tot}

@register.inclusion_tag('datePicker.html')
def datePicker ():
    return {}