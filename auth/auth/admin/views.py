from typing import Any, Dict

from sqlalchemy import select, and_
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin import row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed, FormValidationError

from auth.utils import hash_secret
from auth.models.users import User
from auth.models.clients import Client


__all__ = (
    "ClientView",
    "UserView",
    "ScopeView",
    "RoleView",
    "AccessTokenView",
    "RefreshTokenView",
    "AdminTokenView",
)


class UserView(ModelView):
    fields = ["id", "username", "password", "tokens", "is_superuser"]
    exclude_fields_from_list = ["password"]
    exclude_fields_from_detail = ["password"]
    exclude_fields_from_edit = ["password"]
    exclude_fields_from_create = ["tokens"]

    row_actions = ["view", "edit", "change_password", "delete"]

    def is_accessible(self, request: Request) -> bool:
        return  request.state.user.is_superuser

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}
        session = request.state.session
        new_username = data.get("username")
        another_user_with_same_name_query = select(User).where(User.username == new_username)

        if new_username and (await session.execute(another_user_with_same_name_query)).scalars().first():
            errors["username"] = "User with this name already exists"

        if len(errors) > 0:
            raise FormValidationError(errors)

        return await super().validate(request, data)

    @row_action(
        name="change_password",
        text="Change password",
        confirmation="Are you sure you want to change password for this user?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
        form="""
           <form>
               <div class="mt-3">
                   <input type="text" class="form-control" name="password-input" placeholder="New password">
               </div>
           </form>
           """,
    )
    async def change_password(self, request: Request, pk: Any) -> str:
        data: FormData = await request.form()
        session = request.state.session
        new_password = data.get("password-input")
        obj: User = await self.find_by_pk(request, pk)

        if obj.check_password(new_password):
            raise ActionFailed("The old and new passwords are the same")

        obj.password = hash_secret(new_password)
        await session.commit()
        return "Password was changed successfully"

    async def create(self, request: Request, data: dict[str, Any]) -> User:
        username = data['username']
        password = data['password']
        is_superuser = data['is_superuser']
        return await User.register(request.state.session, username, password, is_superuser)


class ClientView(ModelView):
    fields = ["id", "secret", "name", "description", "access_tokens", "refresh_token", "roles", "personal_scopes"]
    exclude_fields_from_list = ["secret"]
    exclude_fields_from_detail = ["secret"]
    exclude_fields_from_edit = ["secret"]
    exclude_fields_from_create = ["access_tokens", "refresh_token"]

    row_actions = ["view", "edit", "change_secret", "delete"]

    @row_action(
        name="change_secret",
        text="Change secret code",
        confirmation="Are you sure you want to change secret code for this client?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
        form="""
           <form>
               <div class="mt-3">
                   <input type="text" class="form-control" name="secret-input" placeholder="New secret code">
               </div>
           </form>
           """,
    )
    async def change_secret(self, request: Request, pk: Any) -> str:
        data: FormData = await request.form()
        session = request.state.session
        new_secret = data.get("secret-input")
        obj: Client = await self.find_by_pk(request, pk)

        if obj.check_secret(new_secret):
            raise ActionFailed("The old and new secret codes are the same")

        obj.secret = hash_secret(new_secret)
        await session.commit()
        return "Secret code was changed successfully"

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        id_from_form = data.get('id')
        session = request.state.session
        another_client_with_same_id_query = select(Client).where(and_(Client.pk != int(pk), Client.id == id_from_form))

        if (await session.execute(another_client_with_same_id_query)).scalars().first():
            errors = {"id": "Client with this ID already exists"}
            raise FormValidationError(errors)

        return await super().edit(request, pk, data)

    async def create(self, request: Request, data: dict[str, Any]) -> Client:
        return await Client.register(
            session=request.state.session,
            id_=data['id'],
            secret=data['secret'],
            name=data.get('name'),
            description=data.get('description'),
            roles=data.get('roles'),
            personal_scopes=data.get('personal_scopes')
        )


class ScopeView(ModelView):
    fields = ["id", "name", "description", "action", "tokens", "roles", "clients"]


class RoleView(ModelView):
    fields = ["id", "name", "description", "scopes", "clients"]


class AccessTokenView(ModelView):
    fields = ["id", "token", "client", "scopes", "is_active", "expires_at"]


class RefreshTokenView(ModelView):
    fields = ["id", "token", "client", "is_active", "expires_at"]


class AdminTokenView(ModelView):
    fields = ["id", "token", "user", "is_active", "expires_at"]

    def is_accessible(self, request: Request) -> bool:
        return  request.state.user.is_superuser
