from fastapi import FastAPI
from starlette_admin.contrib.sqla import Admin, ModelView


from auth.models import (
    Client,
    Scope,
    AccessToken,
    RefreshToken,
    User,
    Role,
    ClientView,
)
from auth.db import engine


app: FastAPI = FastAPI()

# without nginx redirection
# @app.middleware("http")
# async def redirect_http(request: Request):
#     if request.url.scheme != "https":
#         url = request.url._replace(scheme="https")
#         return RedirectResponse(url=url)

# from routes import ...
# app.include_router(...)

admin = Admin(engine)
admin.add_view(ModelView(User))
admin.add_view(ClientView(Client))
admin.add_view(ModelView(Role))
admin.add_view(ModelView(Scope))
admin.add_view(ModelView(AccessToken))
admin.add_view(ModelView(RefreshToken))
admin.mount_to(app)


@app.get("/")
async def root():
    return {"message": "API root"}
