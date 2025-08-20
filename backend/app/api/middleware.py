# backend/app/api/middleware.py
import json
from pprint import pformat

from fastapi import Request

from app.core.logger import logger


# backend/app/api/middleware.py
async def log_request_middleware(request: Request, call_next):
    """Middleware для логирования входящих запросов"""

    # Логируем детали запроса
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client_host": request.client.host if request.client else None,
        "headers": dict(request.headers),
    }

    logger.info(
        f"Request: {request.method} {request.url.path}\n"
        f"Details:\n{pformat(request_info)}"
    )

    # Читаем и логируем тело запроса только для JSON
    if request.method in ["POST", "PUT", "PATCH"] and request.headers.get(
        "content-type", ""
    ).startswith("application/json"):
        try:
            raw_body = await request.body()
            body = raw_body.decode()

            try:
                json_body = json.loads(body)
                logger.info(
                    f"Request body for {request.url.path}:\n" f"{pformat(json_body)}"
                )
            except json.JSONDecodeError:
                logger.info(f"Raw request body for {request.url.path}:\n{body}")

            # Восстанавливаем тело запроса
            async def get_body():
                return raw_body

            request._body = raw_body
            request.body = get_body

        except Exception as e:
            logger.error(f"Error reading request body: {str(e)}", exc_info=True)

    response = await call_next(request)

    # Логируем ответ
    response_info = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
    }

    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code}\n"
        f"Details:\n{pformat(response_info)}"
    )

    return response
