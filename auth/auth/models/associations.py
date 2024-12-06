from sqlalchemy import Column, Table, ForeignKey
from db.models import Base


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
    Column('token', ForeignKey('tokens.token'), primary_key=True),
    Column('scope_id', ForeignKey('scopes.id'), primary_key=True)
)
