from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel


class Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        from_attributes=True,
    )


class ContactRequest(Base):
    name: str
    email: EmailStr
    message: str
    phone: str
