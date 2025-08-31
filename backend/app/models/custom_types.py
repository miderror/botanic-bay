import os
from typing import Any, Optional

from fastapi_storages.integrations.sqlalchemy import ImageType
from sqlalchemy.engine import Dialect

from app.core.logger import logger


class ResilientImageType(ImageType):
    def process_result_value(
        self, value: Optional[str], dialect: Dialect
    ) -> Optional[Any]:
        if not value:
            return None

        file_path = self.storage.get_path(value)

        if not os.path.exists(file_path):
            logger.warning(
                f"Image file not found on disk, but handled gracefully: {file_path}"
            )
            return None

        return super().process_result_value(value, dialect)
