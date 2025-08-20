import httpx

from app.core.settings import settings


class CDEKAsyncClient(httpx.AsyncClient):
    access_token: str = ""
    token_expires_at: float = 0.0


def get_cdek_async_client(base_url: str = settings.CDEK_BASE_URL) -> CDEKAsyncClient:
    if settings.CDEK_TEST_MODE:
        base_url = settings.CDEK_TEST_BASE_URL

    client = CDEKAsyncClient(base_url=base_url)
    return client
