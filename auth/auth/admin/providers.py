from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

from auth.models import User, AdminToken
from auth.utils import timezone


class AdminProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        self.validate_username(username)

        session = request.state.session
        user = (await session.execute(select(User).where(User.username == username))).scalars().first()

        if not(user and user.check_password(password)):
            raise LoginFailed("Invalid username or password")

        token = await AdminToken.get_or_create_token(session, user.id)

        if remember_me:
            response.set_cookie(key="token", value=token.token, max_age=60 * 60 * 24 * 3)
        else:
            response.set_cookie(key="token", value=token.token, max_age=60 * 60 * 3)

        return response

    @staticmethod
    def validate_username(username: str):
        if len(username) < 5:
            raise FormValidationError(
                {"username": "Ensure username has at least 5 characters"}
            )

        if len(username) > 64:
            raise FormValidationError(
                {"username": "Ensure username has no more than 64 characters"}
            )

    async def is_authenticated(self, request: Request) -> bool:

        if not (token := request.cookies.get("token")):
            return False

        session = request.state.session
        get_token_query = select(AdminToken).where(AdminToken.token == token).options(joinedload(AdminToken.user))
        token_obj = (await session.execute(get_token_query)).scalars().first()

        if not token_obj:
            return False

        if not token_obj.is_active:
            return False

        if token_obj.expires_at < datetime.now(timezone):
            token_obj.is_active = False
            await session.commit()
            return False

        if not (user := token_obj.user):
            return False

        request.state.user = user
        return True

    def get_admin_config(self, request: Request) -> AdminConfig:
        return AdminConfig(
            app_title=f'Hello, {request.state.user.username}!',
            logo_url=None,
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        return AdminUser(username=request.state.user.username, photo_url=None)

    async def logout(self, request: Request, response: Response) -> Response:
        token = request.cookies.get("token")
        session = request.state.session

        get_token_query = select(AdminToken).where(AdminToken.token == token).options(joinedload(AdminToken.user))
        token_obj = (await session.execute(get_token_query)).scalars().first()
        if token_obj:
            token_obj.is_active = False
            await session.commit()

        response.delete_cookie(key="token")
        return response
