"""业务异常定义。"""


class BizError(Exception):
    """业务异常：HTTP 仍返回 200，由全局异常处理器写入 code/message。"""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
