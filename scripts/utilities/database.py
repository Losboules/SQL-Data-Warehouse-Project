"""Safe SQLAlchemy connection factories for local SQL Server and PostgreSQL.

The factories use the names documented in ``.env.example``.  They never embed a
password in source code and they keep the source and serving-warehouse database
choices explicit.
"""
from __future__ import annotations

from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine

from scripts.utilities.config import env_bool, optional_env, required_env


def _sqlserver_server_name() -> str:
    """Build the SQL Server host/instance name without duplicating MSSQLSERVER."""
    server = required_env("SQLSERVER_SERVER")
    instance = optional_env("SQLSERVER_INSTANCE")
    if not instance or instance.upper() == "MSSQLSERVER" or "\\" in server:
        return server
    return f"{server}\\{instance}"


def _sqlserver_engine(database_env: str) -> Engine:
    database = required_env(database_env)
    driver = required_env("SQLSERVER_DRIVER")
    server = _sqlserver_server_name()
    trusted = env_bool("SQLSERVER_TRUSTED_CONNECTION", default=True)
    encrypt = "yes" if env_bool("SQLSERVER_ENCRYPT", default=True) else "no"
    trust_certificate = (
        "yes" if env_bool("SQLSERVER_TRUST_SERVER_CERTIFICATE", default=False) else "no"
    )

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        f"Encrypt={encrypt}",
        f"TrustServerCertificate={trust_certificate}",
        "Connection Timeout=30",
    ]
    if trusted:
        parts.append("Trusted_Connection=yes")
    else:
        parts.extend(
            [
                f"UID={required_env('SQLSERVER_USERNAME')}",
                f"PWD={required_env('SQLSERVER_PASSWORD')}",
            ]
        )

    odbc_connect = ";".join(parts) + ";"
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_connect)}",
        future=True,
        pool_pre_ping=True,
        fast_executemany=True,
    )


def sqlserver_engine() -> Engine:
    """Create an engine for ``NorthstarRetail_ERP`` (or its configured equivalent)."""
    return _sqlserver_engine("SQLSERVER_SOURCE_DATABASE")


def sqlserver_warehouse_engine() -> Engine:
    """Create an engine for ``NorthstarRetail_DW`` (or its configured equivalent)."""
    return _sqlserver_engine("SQLSERVER_WAREHOUSE_DATABASE")


def postgres_engine() -> Engine:
    """Create a PostgreSQL engine using the variables documented in ``.env.example``."""
    username = quote_plus(required_env("POSTGRES_USERNAME"))
    password = quote_plus(required_env("POSTGRES_PASSWORD"))
    host = required_env("POSTGRES_HOST")
    port = required_env("POSTGRES_PORT")
    database = required_env("POSTGRES_DATABASE")
    sslmode = optional_env("POSTGRES_SSLMODE", "prefer")
    return create_engine(
        f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
        f"?sslmode={quote_plus(str(sslmode))}",
        future=True,
        pool_pre_ping=True,
    )
