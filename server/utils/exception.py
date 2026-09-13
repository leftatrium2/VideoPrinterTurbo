from typing import Optional

from utils import const


class VPTException(Exception):
    code = const.GLOBAL_ERR_UNKNOWN
    message = ""

    def __init__(self, code=const.GLOBAL_ERR_UNKNOWN, message="", tr: Optional[Exception] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.tr = tr
