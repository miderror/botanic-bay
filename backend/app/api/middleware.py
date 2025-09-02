import time

from fastapi import Request

from app.core.logger import logger


async def log_request_middleware(request: Request, call_next):
    start_time = time.time()

    method = request.method
    path = request.url.path
    client_host = request.client.host if request.client else "unknown"

    logger.info(f"-> {method} {path} from {client_host}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    logger.info(
        f"<- {method} {path} returned {response.status_code} in {process_time:.2f}ms"
    )

    return response
