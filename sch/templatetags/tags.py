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
    
@register.inclusion_tag("progress-bar.html")
def progressBar (percentage, color):
    return {
        'percent':percentage, 
        'color':color 
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
def posionIcon (width="20px", height="20px", fill="#bbbbbbaa"):
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

@register.inclusion_tag("team.svg")
def teamIcon (width="20px", height="20px", fill="#faed2a99"):
    return {'width': width,'height': height,'fill': fill}

@register.inclusion_tag("sunMoon.svg")
def sunMoon (w='20px', h='20px', fill='white'):
    return {'w': w, 'h': h, 'fill': fill}

@register.simple_tag
def todayYear ():
    return dt.date.today().year 

@register.simple_tag
def todaySch ():
    return 7

@register.inclusion_tag('warn.svg')
def warnIcon (w='15px',h='15px',fill='#ff6688'):
    return {'w': w, 'h': h, 'fill': fill}

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

@register.simple_tag
def showPercent (floating):
    return int(floating*100)

@register.simple_tag
def sumSlotHours (slots):
    total = 0
    for slot in slots:
        total += slot.shift.hours 
    return total

@register.inclusion_tag('reload.svg')
def reloadIcon():
    return {}
@register.inclusion_tag('employee_slot.html') 
def get_employees_slot (workday, employee):
    for slot in workday.slots.all():
        if slot.employee == employee:
            return {"class": "bg-blue-400 text-slate-900", 
                    "weekday": slot.workday.weekday, 
                    "shift": slot.shift}
    return {"class": "bg-slate-700 text-slate-200 text-light", 
                    "weekday": slot.workday.weekday, 
                    "shift": "-"}
    
@register.inclusion_tag('pie-progress.html')
def pie_progress (percent, color="gradient"): 
    if percent > 0 and percent < 1:
        percent = int(percent * 100)
    else:
        percent = int(percent)
    if color == "gradient":
        if percent < 50:
            color = 'bg-red-700'
        elif percent < 75:
            color = 'bg-yellow-600'
        elif percent < 90:
            color = 'bg-green-200'
        else:
            color = 'bg-green-500'
    inverse = 100 - percent
    return {'percent': percent, 'color': color, 'inverse': inverse}

@register.inclusion_tag('pie-progress.css')
def pie_progress_css ():
    return {}

@register.simple_tag
def versionColor (version):
    letters = "A B C D E".split()
    colors = ["orange", "purple", "blue", 'pink', 'emerald']
    if version in letters:
        return colors[letters.index(version)]
    else :
        return "gray"

@register.simple_tag
def scoreColor (score):
    cutoff_values = [0.5, 0.75, 0.9]
    if score > 1:
        score = score / 100
    if score < cutoff_values[0]:
        return "red"
    elif score < cutoff_values[1]:
        return "yellow"
    elif score < cutoff_values[2]:
        return "gray"
    else:
        return "green"
    
@register.simple_tag
def emplHoursSummary (empl, wd):
    return empl.weekHours(wd), empl.periodHours(wd)

@register.simple_tag
def emplWeekAndPeriodHours (empl, wd):
    wk_hrs = empl.weekHours(wd) or 0
    pd_hrs = empl.periodHours(wd) or 0
    return f"W:{int(wk_hrs)}   P:{int(pd_hrs)}"
    
@register.filter(name="getWeekHours")
def employeeWeeklyHours (empl, weekId):
    return empl.get_WeeklyHours(weekId)