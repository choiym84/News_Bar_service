# config.py
import logging
import os

class Config:
    # 개발/운영 전환을 위한 모드
    ENV = os.getenv("ENV", "development")

    # 로그 레벨 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # 로그 레벨 매핑
    LOG_LEVEL_MAP = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    @classmethod
    def get_log_level(cls):
        return cls.LOG_LEVEL_MAP.get(cls.LOG_LEVEL, logging.INFO)
