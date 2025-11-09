"""
SAP Configuration
Connection configuration for SAP OData/RFC integration
"""
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Literal


class SAPConfig(BaseModel):
    """SAP connection configuration"""

    model_config = ConfigDict(frozen=True)

    host: str
    client: str
    user: str
    password: str
    system_number: str = "00"
    connection_type: Literal["odata", "rfc"] = "odata"
    max_retries: int = 3
    timeout: int = 30
    ssl_verify: bool = True
    port: int | None = None

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is not empty"""
        if not v or v.strip() == "":
            raise ValueError("host is required")
        return v

    @field_validator("client")
    @classmethod
    def validate_client(cls, v: str) -> str:
        """Validate client is not empty"""
        if not v or v.strip() == "":
            raise ValueError("client is required")
        return v

    @field_validator("user")
    @classmethod
    def validate_user(cls, v: str) -> str:
        """Validate user is not empty"""
        if not v or v.strip() == "":
            raise ValueError("user is required")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password is not empty"""
        if not v or v.strip() == "":
            raise ValueError("password is required")
        return v
