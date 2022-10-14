from dataclasses import dataclass
import datetime as dt
from typing import List, TypeVar


@dataclass
class Shift:
    name : str
    start : dt.time 
    hours : float 
    
@dataclass
class Employee:
    name : str
    fte_14_day : int
    shifts : List[Shift]
    
    

[
    {
        'name':'Josh',
        'fte_14_day':50,
        'shifts':[
    }
]