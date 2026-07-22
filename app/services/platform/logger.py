import json
import logging
from typing import Any


class PlatformLogger:
    def __init__(self, logger_name: str = "app.platform"):
        self._logger = logging.getLogger(logger_name)

    def info(self, event: str, **payload: Any) -> None:
        self._logger.info(self._format(event, payload))

    def warning(self, event: str, **payload: Any) -> None:
        self._logger.warning(self._format(event, payload))

    def error(self, event: str, **payload: Any) -> None:
        self._logger.error(self._format(event, payload))

    def _format(self, event: str, payload: dict[str, Any]) -> str:
        return json.dumps({"event": event, **payload}, ensure_ascii=False, default=str)
