"""推荐模块配置：读取 backend/.env，与后端共用数据库和 Redis。"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

RECOMMENDER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = RECOMMENDER_DIR.parent
BACKEND_ENV = PROJECT_ROOT / "backend" / ".env"

# 优先读取后端配置，环境变量仍然拥有最高优先级
load_dotenv(BACKEND_ENV, override=False)


def _java_major(java_home: str) -> int:
    """探测 JAVA_HOME 的 Java 主版本，失败返回 0。"""
    java_exe = Path(java_home) / "bin" / "java.exe"
    if not java_exe.exists():
        java_exe = Path(java_home) / "bin" / "java"
    if not java_exe.exists():
        return 0
    try:
        result = subprocess.run(
            [str(java_exe), "-version"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        output = f"{result.stdout}\n{result.stderr}"
        match = re.search(r'version "(\d+)(?:\.(\d+))?', output)
        if not match:
            return 0
        major = int(match.group(1))
        # Java 1.8 的版本号格式为 1.8.0_xxx
        if major == 1 and match.group(2):
            return int(match.group(2))
        return major
    except Exception:
        return 0


def _detect_java_home() -> str:
    """优先使用 Java 17+，避免系统默认 Java 8 导致 Spark 兼容性问题。"""
    configured = os.getenv("JAVA_HOME", "").strip()
    if configured and _java_major(configured) >= 17:
        return configured

    candidates: list[Path] = []
    for base in (
        Path("C:/Program Files/Java"),
        Path("C:/Program Files/Eclipse Adoptium"),
        Path("C:/Program Files/Microsoft"),
        Path("C:/Program Files/Amazon Corretto"),
    ):
        if base.exists():
            candidates.extend(path for path in base.iterdir() if path.is_dir())

    preferred = [
        path
        for path in candidates
        if any(token in path.name.lower() for token in ("17", "21"))
        and (path / "bin" / "java.exe").exists()
    ]
    if preferred:
        # 17 对 Spark 4.0 的兼容性最稳；没有 17 时使用 21
        preferred.sort(key=lambda p: (0 if "17" in p.name else 1, p.name))
        return str(preferred[0])
    return ""


_detected_java_home = _detect_java_home()
if _detected_java_home:
    # 必须强制覆盖：系统可能默认 JAVA_HOME 指向 Java 8
    os.environ["JAVA_HOME"] = _detected_java_home
    java_bin = Path(_detected_java_home) / "bin"
    if java_bin.exists():
        os.environ["PATH"] = f"{java_bin}{os.pathsep}{os.environ.get('PATH', '')}"

os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")


def _parse_mysql_url(url: str) -> dict[str, str | int]:
    """把 SQLAlchemy 风格 URL 拆成 PyMySQL 连接参数。"""
    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError(f"DATABASE_URL 格式错误: {url}")
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/ecommerce").lstrip("/"),
    }


@dataclass(frozen=True)
class RecommenderSettings:
    """推荐任务参数。"""

    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://root:276367@127.0.0.1:3306/ecommerce?charset=utf8mb4",
        )
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    )
    spark_master: str = field(
        default_factory=lambda: os.getenv("SPARK_MASTER", "local[*]")
    )
    rank: int = field(default_factory=lambda: int(os.getenv("ALS_RANK", "10")))
    iterations: int = field(
        default_factory=lambda: int(os.getenv("ALS_ITERATIONS", "10"))
    )
    reg_param: float = field(
        default_factory=lambda: float(os.getenv("ALS_LAMBDA", "0.01"))
    )
    implicit_prefs: bool = field(
        default_factory=lambda: os.getenv("ALS_IMPLICIT", "true").lower()
        in {"1", "true", "yes"}
    )
    alpha: float = field(
        default_factory=lambda: float(os.getenv("ALS_ALPHA", "40.0"))
    )
    user_top_n: int = field(
        default_factory=lambda: int(os.getenv("ALS_USER_TOP_N", "20"))
    )
    item_top_n: int = field(
        default_factory=lambda: int(os.getenv("ALS_ITEM_TOP_N", "10"))
    )
    jdbc_version: str = field(
        default_factory=lambda: os.getenv("MYSQL_JDBC_VERSION", "8.4.0")
    )
    jdbc_jar: Path = field(
        default_factory=lambda: Path(
            os.getenv(
                "MYSQL_JDBC_JAR",
                str(RECOMMENDER_DIR / "jars" / "mysql-connector-j-8.4.0.jar"),
            )
        )
    )
    result_file: Path = field(default_factory=lambda: PROJECT_ROOT / "evaluation_result.md")

    @property
    def mysql(self) -> dict[str, str | int]:
        return _parse_mysql_url(self.database_url)

    @property
    def jdbc_url(self) -> str:
        db = self.mysql
        return (
            f"jdbc:mysql://{db['host']}:{db['port']}/{db['database']}"
            "?useSSL=false&allowPublicKeyRetrieval=true"
            "&serverTimezone=Asia/Shanghai&characterEncoding=utf8"
        )


settings = RecommenderSettings()
DATA_DIR = RECOMMENDER_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
