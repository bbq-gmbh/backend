class OverTimeCalculator:
    def __init__(self, hours_worked, worktime_hours_day, overtime_yellow_border):
        self.hours_worked = hours_worked
        self.worktime_hours_day = worktime_hours_day
        self.overtime_yellow_border = overtime_yellow_border
        self.overtime_red_border = overtime_yellow_border + 10


    def calculate_overtime(self, hours_worked, worktime_hours_day):
        if hours_worked <= worktime_hours_day:
            return 0
        elif hours_worked > worktime_hours_day:
            if hours_worked > 6:
                working_break = 45
                overtime_hours = hours_worked - working_break - worktime_hours_day
                return overtime_hours
            elif hours_worked > 4:
                working_break = 15
                overtime_hours = hours_worked - working_break - worktime_hours_day
                return overtime_hours
            else:
                return 0
        return None
    def overtime_warning(self, overtime_hours, overtime_yellow_border, overtime_red_border):
        if overtime_hours > overtime_yellow_border:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Overtime Warning: Yellow your overtime is {overtime_hours} hours.\nThe limit is {overtime_yellow_border} hours.\nYour Supervisor will be informed."
        )
        elif overtime_hours > overtime_red_border:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Overtime Warning: Red your overtime is {overtime_hours} hours.\nThe limit is {overtime_red_border} hours.\nYour Supervisor will be informed.",
        )
        return None

    