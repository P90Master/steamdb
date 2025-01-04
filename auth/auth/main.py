from fastapi import FastAPI
from starlette_admin.contrib.sqla import Admin

from auth.models import (
    Client,
    Scope,
    AccessToken,
    RefreshToken,
    AdminToken,
    User,
    Role,
)
from auth.admin import (
    ClientView,
    UserView,
    ScopeView,
    RoleView,
    AccessTokenView,
    RefreshTokenView,
    AdminTokenView,
    AdminProvider,
)
from auth.db import engine
from auth.core.config import settings


app: FastAPI = FastAPI()

# without nginx redirection
# @app.middleware("http")
# async def redirect_http(request: Request):
#     if request.url.scheme != "https":
#         url = request.url._replace(scheme="https")
#         return RedirectResponse(url=url)

# from routes import ...
# app.include_router(...)

admin = Admin(
    engine=engine,
    auth_provider=AdminProvider()
)
admin.add_view(UserView(User))
admin.add_view(ClientView(Client))
admin.add_view(RoleView(Role))
admin.add_view(ScopeView(Scope))
admin.add_view(AccessTokenView(AccessToken))
admin.add_view(RefreshTokenView(RefreshToken))
admin.add_view(AdminTokenView(AdminToken))
admin.mount_to(app)


@app.get("/")
async def root():
    return {"message": "API root"}
