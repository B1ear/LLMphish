"""
简单的内存级存储，用于原型阶段管理邮件与检测结果。
后续可以很容易替换为 Redis / 数据库。
"""

from typing import Dict, Any
from uuid import uuid4


class InMemoryStore:
    def __init__(self) -> None:
        self.emails: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.screenshots: Dict[str, bytes] = {}  # email_id -> screenshot image bytes

    def save_email(self, content: str, meta: Dict[str, Any]) -> str:
        email_id = uuid4().hex
        self.emails[email_id] = {
            "content": content,
            "meta": meta,
        }
        return email_id

    def save_screenshot(self, email_id: str, image_bytes: bytes) -> None:
        """保存邮件截图"""
        self.screenshots[email_id] = image_bytes

    def get_screenshot(self, email_id: str) -> bytes | None:
        """获取邮件截图"""
        return self.screenshots.get(email_id)

    def get_email(self, email_id: str) -> Dict[str, Any]:
        return self.emails.get(email_id)  # type: ignore[return-value]

    def save_result(self, email_id: str, result: Dict[str, Any]) -> None:
        self.results[email_id] = result

    def get_result(self, email_id: str) -> Dict[str, Any]:
        return self.results.get(email_id, {})  # type: ignore[return-value]


store = InMemoryStore()


