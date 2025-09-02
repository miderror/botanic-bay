import os
from typing import Any, Optional

from fastapi_storages.integrations.sqlalchemy import ImageType
from PIL import UnidentifiedImageError
from sqlalchemy.engine import Dialect

from app.core.logger import logger


class ResilientImageType(ImageType):
    def process_result_value(
        self, value: Optional[str], dialect: Dialect
    ) -> Optional[Any]:
        if not value:
            return None

        file_path = self.storage.get_path(value)

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            logger.warning(
                f"Image file not found or is empty, handled gracefully: {file_path}"
            )
            return None

        try:
            return super().process_result_value(value, dialect)
        except UnidentifiedImageError:
            logger.error(
                f"Cannot identify image file (corrupted or invalid format): {file_path}"
            )
            return None
        except Exception as e:
            logger.error(f"Error processing image file {file_path}: {e}")
            return None
