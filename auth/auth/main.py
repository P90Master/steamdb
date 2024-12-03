from fastapi import FastAPI

app: FastAPI = FastAPI()

# without nginx redirection
# @app.middleware("http")
# async def redirect_http(request: Request):
#     if request.url.scheme != "https":
#         url = request.url._replace(scheme="https")
#         return RedirectResponse(url=url)

# from routes import ...
# app.include_router(...)

@app.get("/")
async def root():
    return {"message": "API root"}
