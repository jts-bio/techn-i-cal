# Workday Rendering

====================================

Employee
    if @AM and @NEXT-PM
            --> +TURNAROUND [ORANGE]
    if @TDO or @PTO
    && Working Today
            --> +CONFLICT [RED]

Slot
    .employee in me?
        --> Hide TEMPLATE-EMPL-BUTTON
    @template != @employee
