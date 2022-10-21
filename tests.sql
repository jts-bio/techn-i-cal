-- SQLBook: Code
SELECT * FROM sch_shift

SELECT * FROM sch_employee

SELECT id FROM sch_employee
WHERE name = 'CHERYL'

-- SQLBook: Code

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