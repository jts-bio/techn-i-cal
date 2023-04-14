# FlowRate

`PHARMACY SCHEDULING SOFTWARE`

--------------------------------

Models 
=====================================

Employee
--------------------------------
yaml```
====== EMPLOYEE ======
x
[FIELDS]
    - name
    - fte_14_day 
    - shifts_trained 
    - shifts_available
    - streak_pref 
    - cls
    - evening_pref

[CALCULATED_FIELDS]
    + fte 

[METHODS]
    * url()
    * weekly_hours()
    * weekly_hours_perc()
    * period_hours()
    * period_hours_perc()

```
