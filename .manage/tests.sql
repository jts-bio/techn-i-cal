-- SQLBook: Code
SELECT * FROM sch_shift

SELECT name, id
FROM   sch_employee
WHERE  "evening_pref" == 1

SELECT name, id 
FROM sch_employee
WHERE name = 'CHERYL'

SELECT COUNT(*)
FROM sch_slot
WHERE employee_id = 17
-- Cheryl

SELECT * FROM sch_slot
WHERE workday_id = 299

SELECT * from sch_shiftpreference
WHERE employee_id = (
    SELECT id 
    FROM sch_employee
    WHERE name = 'JOSH' 
)

SELECT * FROM "sch_employee" 
WHERE "sch_employee"."id" 
    IN (1, 6, 7, 13, 16, 18, 1)

SELECT * 
FROM sch_slot
WHERE workday_id = (
    SELECT id
    FROM sch_workday
    WHERE slug == '2022-10-31'
) 

