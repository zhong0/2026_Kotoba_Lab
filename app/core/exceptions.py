class AppError(Exception):
    """應用層錯誤，由全域 exception handler 轉成統一的 JSON 錯誤格式。"""

    def __init__(self, error_message: str, error_code: str = "APP_ERROR", status_code: int = 400):
        self.error_message = error_message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(error_message)


class DatabaseError(AppError):
    """資料庫操作失敗。DAO 層丟出，handler 統一回 500。"""

    def __init__(self, error_message: str):
        super().__init__(error_message, error_code="DATABASE_ERROR", status_code=500)
