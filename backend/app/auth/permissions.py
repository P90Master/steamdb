from fastapi import HTTPException
from starlette.requests import Request

from .scopes import Scope


class BasePermission:
    def __call__(self, request: Request):
        if not self.has_permission(request):
            raise HTTPException(status_code=403, detail="Not enough permissions")

    @classmethod
    def has_permission(cls, request: Request) -> bool:
        return True


class IsAuthenticated(BasePermission):
    def __call__(self, request: Request):
        if not self.is_authenticated(request):
            raise HTTPException(status_code=401, detail="Not authorized")

    @classmethod
    def is_authenticated(cls, request: Request) -> bool:
        return bool(getattr(request.state, 'user', False))

    @classmethod
    def has_permission(cls, request: Request) -> bool:
        return True


class IsAuthenticatedAndHasScopes(IsAuthenticated):
    """
    AND - between inherited scopes
    OR - between scopes in __class__.SCOPES

    Example:
        class CanRead(IsAuthenticatedAndHasScopes):
            SCOPES = Scope.READ

        class IsStaff(CanRead):
            SCOPES = (Scope.CREATE, Scope.UPDATE, Scope.DELETE)

    For access to endpoints with "IsStuff" dependency user must be authenticated,
    has Scope.READ and has one of Scope.CREATE, Scope.UPDATE or Scope.DELETE
    """
    SCOPES: tuple[str] | str = None

    def __call__(self, request: Request):
        super().__call__(request)

        if self.is_admin(request):
            return

        if not all((cls.has_permission(request) for cls in self.__class__.__mro__[:-1])):
            raise HTTPException(status_code=403, detail="Not enough permissions")

    @staticmethod
    def is_admin(request: Request) -> bool:
        return Scope.ALL in request.state.user.get("scopes") or Scope.SUPERUSER in request.state.user.get("scopes")

    @classmethod
    def has_permission(cls, request: Request) -> bool:
        if cls.SCOPES is None:
            return True

        user_scopes = request.state.user.get("scopes", [])

        if isinstance(cls.SCOPES, str):
            return cls.SCOPES in user_scopes

        return any(scope in user_scopes for scope in cls.SCOPES)


class IsAdmin(IsAuthenticatedAndHasScopes):
    SCOPES = Scope.ALL


class CanRead(IsAuthenticatedAndHasScopes):
    SCOPE = Scope.READ


class CanCreate(IsAuthenticatedAndHasScopes):
    Scope = Scope.CREATE


class CanUpdate(IsAuthenticatedAndHasScopes):
    SCOPE = Scope.UPDATE


class CanDelete(IsAuthenticatedAndHasScopes):
    SCOPES = Scope.DELETE


class CanSendPackages(IsAuthenticatedAndHasScopes):
    SCOPES = Scope.PACKAGE


class CanRegisterTasks(IsAuthenticatedAndHasScopes):
    SCOPES = Scope.TASKS


class IsModerator(CanRead, CanCreate, CanUpdate, CanDelete, CanRegisterTasks):
    pass


class IsWorker(CanSendPackages):
    pass


class Permissions:
    is_authenticated = IsAuthenticated()
    is_worker = IsWorker()
    is_moderator = IsModerator()
    is_admin = IsAdmin()
    can_read = CanRead()
    can_create = CanCreate()
    can_update = CanUpdate()
    can_delete = CanDelete()
    can_send_packages = CanSendPackages()
    can_register_tasks = CanRegisterTasks()
