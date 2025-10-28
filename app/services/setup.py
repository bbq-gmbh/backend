from app.core.exceptions import DomainError, UserAlreadyExistsError
from app.repositories.server_store import ServerStoreRepository
from app.repositories.user import UserRepository
from app.schemas.setup import SetupCreate
from app.services.user import UserService


class SetupService:
    def __init__(
        self, user_repo: UserRepository, server_store_repo: ServerStoreRepository
    ):
        self.user_repo = user_repo
        self.server_store_repo = server_store_repo
        self.session = user_repo.session

    def check_is_setup(self) -> bool:
        return self.server_store_repo.try_get() is not None

    def setup_create(self, setup_in: SetupCreate):
        if self.server_store_repo.try_get():
            raise DomainError("Application cannot be setup again in this state")

        server_store = self.server_store_repo.create(setup_in.server_store)

        user_in = setup_in.user

        UserService._validate_username(user_in.username)
        UserService._validate_password(user_in.password)

        if self.user_repo.get_user_by_username(user_in.username):
            raise UserAlreadyExistsError(user_in.username)

        user = self.user_repo.create_user(user_in)
        user.is_superuser = True

        self.session.commit()

        self.session.refresh(server_store)
        self.session.refresh(user)

        return user
