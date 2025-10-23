from app.models.user import User
from app.services.employee import EmployeeService


class AuthorizationService:
    @staticmethod
    def can_access_read(actor: User, target: User) -> bool:
        """Check if actor can read target's data.

        Args:
            actor: The user attempting to read.
            target: The user whose data is being accessed.

        Returns:
            True if actor is superuser, same user, or higher/equal in hierarchy, False otherwise.
        """
        if actor.is_superuser:
            return True

        if actor.id == target.id:
            return True

        # Check hierarchy if both have employee records
        if actor.employee and target.employee:
            return EmployeeService.is_higher(actor.employee, target.employee, same=True)

        return False

    @staticmethod
    def can_access_write(actor: User, target: User) -> bool:
        """Check if actor can write/modify target's data.

        Args:
            actor: The user attempting to write.
            target: The user whose data is being modified.

        Returns:
            True if actor is superuser or same user, False otherwise.
        """
        if actor.is_superuser:
            return True

        if actor.id == target.id:
            return True

        return False
