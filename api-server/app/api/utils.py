from fastapi.responses import JSONResponse
from functools import wraps
from typing import Callable, Any
from app.utils.api_bans import ban_handler, TemporaryBanError


def check_api_ban(data_source: str, endpoint: str) -> Callable:
    """
    Decorator that checks if an API endpoint is temporarily banned.
    If it is banned, returns a JSON error response; otherwise, proceeds.

    Usage:
    ```python
    @app.get("/endpointname")
    @check_api_ban(data_source="datasourcename", endpoint="/endpointname")
    async def get_data(request: Request):
        # Your endpoint logic here
        return {"message": "Data retrieved successfully."}
    ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                await ban_handler.raise_if_blocked(data_source, endpoint)
            except TemporaryBanError as e:

                return JSONResponse(
                    status_code=429,
                    content={
                        "message": str(e),
                        "blocked_until": e.blocked_until.isoformat(),
                    },
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
