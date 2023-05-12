import datetime as dt
from pprint import pprint
import os, pathlib
import random


DAYCHOICES = (
        (0, 'Sun'),
        (1, 'Mon'),
        (2, 'Tue'),
        (3, 'Wed'),
        (4, 'Thu'),
        (5, 'Fri'),
        (6, 'Sat')
    )

WEEKABCHOICES  =   ((0, 'A'),(1, 'B'))

TODAY                   = dt.date.today ()
TEMPLATESCH_STARTDATE   = dt.date (2020,1,12)

SCH_STARTDATE_SET       = [(TEMPLATESCH_STARTDATE + dt.timedelta(days=42*i)) for i in range (50)]

PRIORITIES  = (
                ('L', 'Low'),
                ('M', 'Medium'),
                ('H', 'High'),
                ('U', 'Urgent'),
            )

PREF_SCORES  = (
                ('SP', 'Strongly Prefer'),
                ('P', 'Prefer'),
                ('N', 'Neutral'),
                ('D', 'Dislike'),
                ('SD', 'Strongly Dislike'),
            )

PTO_STATUS_CHOICES  = (
                    ('Pending',  'Pending'),
                    ('Approved', 'Approved'),
                    ('Denide',   'Denied'),
                )


def group_dates_by_year(dates):
    """
    Groups a list of dates by the year into a dictionary.

    Parameters:
        dates (list): A list of date strings in the format '%Y-%m-%d'.

    Returns:
        dict: A dictionary with the year as the key and a list of dates as the value.
    """
    grouped_dates = {}
    for date in dates:
        year = date.year
        if year in grouped_dates:
            grouped_dates[year].append(date)
        else:
            grouped_dates[year] = [date]
    return grouped_dates




class Images:
    
    SEAMLESS_OPTIONS = ["/static/img/" + x for x in os.listdir('static/img/') if 'tile' in x.lower() ]
    
    def randomSeamlessChoice () -> str:
        return random.choice(Images.SEAMLESS_OPTIONS)

    class Profile:
        CUTE_ROBOT_1    = '/static/img/CuteRobot-01.png'
        CUTE_ROBOT_2    = '/static/img/CuteRobot-02.png'
        TECHNO_BIRD     = '/static/img/bird-profile-techno.png'
        YODA_ORIGAMI    = '/static/img/yoda-origami.png'
    
    
    
    class BtnBackgrounds: 
        EMPL_GRID = "https://media.discordapp.net/attachments/1015278074197200957/1094929093620936795/jsteinbecker_None_eb040ab7-f9c3-4ecf-bbe3-38abf3cbabaa.png?width=1980&height=1320"