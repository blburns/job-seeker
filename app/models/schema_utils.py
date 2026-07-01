"""Database schema helpers for multi-DB support."""

import os


def db_schema(name: str):
    """Return schema dict for PostgreSQL, empty for SQLite."""
    if os.environ.get('DB_TYPE', 'sqlite') == 'postgresql':
        return {'schema': name}
    return {}


def fk_ref(schema: str, table: str, column: str = 'id'):
    """Build foreign key reference string."""
    if os.environ.get('DB_TYPE', 'sqlite') == 'postgresql':
        return f'{schema}.{table}.{column}'
    return f'{table}.{column}'


def auth_table_args(*constraints):
    """Build __table_args__ with optional auth schema on PostgreSQL."""
    if os.environ.get('DB_TYPE', 'sqlite') == 'postgresql':
        return constraints + ({'schema': 'auth'},)
    return constraints if constraints else {}
