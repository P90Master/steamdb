from starlette_admin.contrib.sqla import ModelView


__all__ = (
    "ClientView",
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
