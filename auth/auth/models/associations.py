from sqlalchemy import Column, Table, ForeignKey
from auth.db import Base


__all__ = [
    'client_scope_association',
    'client_role_association',
    'scope_role_association',
    'token_scope_association'
]


client_scope_association = Table(
    'client_scope',
    Base.metadata,
    Column('client_id', ForeignKey('clients.id'), primary_key=True),
    Column('scope_id', ForeignKey('scopes.id'), primary_key=True)
)
client_role_association = Table(
    'client_role',
    Base.metadata,
    Column('client_id', ForeignKey('clients.id'), primary_key=True),
    Column('role_id', ForeignKey('roles.id'), primary_key=True)
)
scope_role_association = Table(
    'scope_role',
    Base.metadata,
    Column('scope_id', ForeignKey('scopes.id'), primary_key=True),
    Column('role_id', ForeignKey('roles.id'), primary_key=True)
)
token_scope_association = Table(
    'token_scope',
    Base.metadata,
    Column('token', ForeignKey('accesstokens.id'), primary_key=True),
    Column('scope_id', ForeignKey('scopes.id'), primary_key=True)
)
