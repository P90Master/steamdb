from pydantic import BaseModel


__all__ = (
    'AuthenticationRequestSchema',
    'AuthenticationResponseSchema',
    'TokenIntrospectionRequestSchema',
    'TokenIntrospectionResponseSchema',
    'RefreshTokenRequestSchema',
    'RefreshTokenResponseSchema',
)


class AuthenticationRequestSchema(BaseModel):
    client_id: str
    client_secret: str
    scopes: list[str] | None = None


class AuthenticationResponseSchema(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class TokenIntrospectionRequestSchema(BaseModel):
    access_token: str


class TokenIntrospectionResponseSchema(BaseModel):
    is_active: bool
    client_id: str
    scopes: list[str] | None = None
    expires_at: int


class RefreshTokenRequestSchema(BaseModel):
    """
    In standard RFC 6749, refresh token is associated with a set of scopes that were issued when
    access token and refresh token were issued. That is, in the standard, when a client uses a refresh token,
    it must also provide its ID and secret.

    In this case, I consider this inappropriate,
    refresh token will be used to confirm that client has successfully authenticated earlier,
    in order to avoid re-providing its ID and secret.
    """
    refresh_token: str
    scopes: list[str] | None = None


class RefreshTokenResponseSchema(BaseModel):
    access_token: str
    expires_in: int
