from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )