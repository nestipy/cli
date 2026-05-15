from typing import Callable, Optional, Type, Union, cast

from nestipy.common import Request
from nestipy.ioc import RequestContextContainer, create_type_annotated
from nestipy.metadata import SetMetadata

PUBLIC = "__public__"


def get_user_from_request(
    _name: str,
    _token: Optional[str],
    _type_ref: Type,
    _request_context: RequestContextContainer,
):
    context = _request_context.execution_context
    if context is not None:
        request = context.get_request()
        return cast(Request, request).user if hasattr(request, "user") else None
    return None


AuthUser = create_type_annotated(get_user_from_request, "user")


def IsPublic() -> Callable[[Union[Type, Callable]], Union[Type, Callable]]:
    return SetMetadata(PUBLIC, True)
