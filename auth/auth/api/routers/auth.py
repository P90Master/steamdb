from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from auth.db import get_db
from auth.core.config import settings
from auth.models import Client, AccessToken, RefreshToken, Scope
from auth.api.schemas import (
    AuthenticationRequestSchema,
    AuthenticationResponseSchema,
    TokenIntrospectionRequestSchema,
    TokenIntrospectionResponseSchema,
    RefreshTokenRequestSchema,
    RefreshTokenResponseSchema,
)

router = APIRouter()


def make_action_to_scope_mapping(scopes: list[Scope]) -> dict[str, Scope]:
    return {scope.action: scope for scope in scopes}


@router.post('/token', response_model=AuthenticationResponseSchema, status_code=200)
async def get_access_token(request: AuthenticationRequestSchema, db: AsyncSession = Depends(get_db)):
    client = (await db.execute(select(Client).where(Client.id == request.client_id))).scalars().one_or_none()

    if not client:
        raise HTTPException(status_code=401, detail=f'invalid_client')

    if not client.check_secret(request.client_secret):
        raise HTTPException(status_code=401, detail=f'invalid_client')

    client_scopes = await client.get_all_scopes(session=db)
    selected_scopes: list[Scope]

    if requested_scopes := request.scopes:
        selected_scopes = []
        scope_registry = make_action_to_scope_mapping(client_scopes)

        for requested_scope_action in requested_scopes:
            if not (accessible_scope := scope_registry.get(requested_scope_action)):
                raise HTTPException(status_code=403, detail=f'invalid_scope')

            selected_scopes.append(accessible_scope)
    else:
        selected_scopes = client_scopes

    client_pk = client.pk
    access_token = await AccessToken.create_token(session=db, client_pk=client_pk, scopes=selected_scopes)
    refresh_token = await RefreshToken.get_or_create_token(session=db, client_pk=client_pk)
    return AuthenticationResponseSchema(
        access_token=access_token.token,
        # token_type=settings.TOKEN_TYPE,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        refresh_token=refresh_token.token
    )


@router.post('/token_info', response_model=TokenIntrospectionResponseSchema, status_code=200)
async def get_token_info(request: TokenIntrospectionRequestSchema, db: AsyncSession = Depends(get_db)):
    token = (
        await db.execute(
            select(AccessToken).where(
                AccessToken.token == request.access_token
            ).options(
                joinedload(AccessToken.client),
                joinedload(AccessToken.scopes)
            )
        )
    ).unique().scalars().one_or_none()

    if not token:
        raise HTTPException(status_code=401, detail=f'invalid_token')

    if not (client := token.client):
        raise HTTPException(status_code=401, detail=f'invalid_token')

    return TokenIntrospectionResponseSchema(
        is_active=token.is_active,
        client_id=client.id,
        scopes=[scope.action for scope in token.scopes],
        expires_at=int(token.expires_at.timestamp())
    )


@router.post('/token_refresh', response_model=RefreshTokenResponseSchema, status_code=200)
async def token_refresh(request: RefreshTokenRequestSchema, db: AsyncSession = Depends(get_db)):
    token = (
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == request.refresh_token
            ).options(
                joinedload(RefreshToken.client)
            )
        )
    ).unique().scalars().one_or_none()

    if not token:
        raise HTTPException(status_code=401, detail=f'invalid_token')

    if not (client := token.client):
        raise HTTPException(status_code=401, detail=f'invalid_token')

    client_scopes = await client.get_all_scopes(session=db)
    selected_scopes: list[Scope]

    if requested_scopes := request.scopes:
        selected_scopes = []
        scope_registry = make_action_to_scope_mapping(client_scopes)

        for requested_scope_action in requested_scopes:
            if not (accessible_scope := scope_registry.get(requested_scope_action)):
                raise HTTPException(status_code=403, detail=f'invalid_scope')

            selected_scopes.append(accessible_scope)
    else:
        selected_scopes = client_scopes

    access_token = await AccessToken.create_token(session=db, client_pk=client.pk, scopes=selected_scopes)
    return RefreshTokenResponseSchema(
        access_token=access_token.token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )