from datetime import time
from pprint import pprint
import os, pathlib
import random

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