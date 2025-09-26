from typing import Optional

class TimeServices:
    def __init__(self):
        self.overtime_account = 0

    def calculate_break(self, work_hours: float) -> int:
        """
        Calculates the break time based on work hours.

        Args:
            work_hours (float): The number of hours worked.

        Returns:
            int: The break time in minutes.
        """
        if work_hours > 6:
            return 30
        elif work_hours > 4:
            return 15
        else:
            return 0

    def calculate_overtime(self, work_hours: float, rule_work_hours: float) -> Optional[str]:
        """
        Calculates overtime and manages the overtime account.

        Args:
            work_hours (float): The actual number of hours worked.
            rule_work_hours (float): The standard number of hours for the workday.

        Returns:
            Optional[str]: A message if overtime exceeds certain thresholds, otherwise None.
        """
        overtime = work_hours - rule_work_hours
        if overtime > 0:
            self.overtime_account += overtime

        if self.overtime_account > 35:
            return "Warnung: Überstundenkonto überschreitet 35 Stunden!"
        elif self.overtime_account > 25:
            return "Hinweis: Überstundenkonto überschreitet 25 Stunden."
        else:
            return None
    
    def calculate_break_with_overtime(self, work_hours: float, core_work_hours: float = 7.0) -> int: #
        """
        Calculates break time considering overtime in addition to regular work hours.

        Args:
            work_hours (float): The total number of hours worked (including overtime).
            core_work_hours (float): The standard number of hours for the workday. Default is 7.

        Returns:
            int: The break time in minutes.
        """
        total_work_hours = work_hours  # Simplified as the condition was redundant
        return self.calculate_break(total_work_hours)
    # add DB connection here if needed