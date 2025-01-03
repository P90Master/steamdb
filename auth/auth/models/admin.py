from typing import Any

from sqlalchemy import select
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin import row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed, FormValidationError

from auth.utils import hash_secret
from .users import User


__all__ = (
    "ClientView",
    "UserAdmin",
)


class ClientView(ModelView):
    fields = [
        "id",
        "secret",
        "name",
        "description",
        "access_tokens",
        "refresh_token",
        "roles",
        "personal_scopes"
    ]
    form_include_pk = True


class UserAdmin(ModelView):
    fields = ["id", "username", "password"]
    exclude_fields_from_list = ["password"]
    exclude_fields_from_detail = ["password"]
    exclude_fields_from_edit = ["password"]

    row_actions = ["view", "edit", "change_password", "delete"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}
        session = request.state.session
        new_username = data.get("username")

        if new_username and (await session.execute(select(User).where(User.username == new_username))).scalars().all():
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
        return await User.register(username, password, request.state.session)
