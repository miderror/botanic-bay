import hashlib
import json
from enum import Enum
from typing import Union


def redis_key(base: str, params: dict | None = None, use_hash: bool = False) -> str:
    if not params:
        return base
    params_str = json.dumps(params, sort_keys=True, separators=(",", ":"))
    if use_hash:
        params_str = hashlib.md5(params_str.encode()).hexdigest()
    return f"{base}:{params_str}"


class RedisKeyBuilder:
    def __init__(self, service: str):
        self.service = service

    def build(
        self,
        key: Union[str, Enum],
        params: dict = None,
        *,
        use_hash: bool = False,
    ) -> str:
        key_name = key.value if isinstance(key, Enum) else key
        base = f"{self.service}:{key_name}"
        return redis_key(base, params or {}, use_hash=use_hash)
