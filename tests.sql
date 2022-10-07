SELECT * FROM sch_shift

SELECT * FROM sch_employee

SELECT id FROM sch_employee
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

