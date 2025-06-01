import logging
from colorlog import ColoredFormatter

def setup_logger():
    logging.basicConfig(level=logging.WARNING, force=True)

    formatter = ColoredFormatter(
        "%(log_color)s[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    # 🎯 반드시: 외부 로그 핸들러 제거 후 레벨 조정
    for name in [
        "sentence_transformers.SentenceTransformer",
        "httpx",
        "sqlalchemy.engine", "sqlalchemy.dialects", "sqlalchemy.pool", "sqlalchemy.orm"
    ]:
        lib_logger = logging.getLogger(name)
        lib_logger.handlers.clear()     # 💥 기존 핸들러 제거
        lib_logger.setLevel(logging.WARNING)  # ⚠️ 로그 레벨 제한
        lib_logger.propagate = False