"""PySpark ALS 离线训练：用户推荐、物品相似度、热销榜。

运行：cd recommender && python train_als.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pymysql
import redis
from pyspark.ml.recommendation import ALS
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from config import DATA_DIR, settings

JDBC_DRIVER_CLASS = "com.mysql.cj.jdbc.Driver"
MAVEN_BASE = "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j"


def ensure_jdbc_jar() -> Path | None:
    """确保 MySQL JDBC 驱动存在；下载失败时后续自动回退 CSV。"""
    jar = settings.jdbc_jar
    if jar.exists() and jar.stat().st_size > 100_000:
        return jar
    jar.parent.mkdir(parents=True, exist_ok=True)
    url = (
        f"{MAVEN_BASE}/{settings.jdbc_version}/"
        f"mysql-connector-j-{settings.jdbc_version}.jar"
    )
    print(f"[ALS] 首次运行，下载 MySQL JDBC 驱动：{url}")
    try:
        urllib.request.urlretrieve(url, jar)
        print(f"[ALS] JDBC 驱动已保存：{jar} ({jar.stat().st_size / 1024:.0f} KB)")
        return jar
    except Exception as exc:
        print(f"[ALS] JDBC 驱动下载失败（将回退 CSV）：{exc}")
        return None


def build_spark(app_name: str, jdbc_jar: Path | None = None) -> SparkSession:
    """创建 local 模式 SparkSession。"""
    builder = (
        SparkSession.builder.master(settings.spark_master)
        .appName(app_name)
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.warehouse.dir", str(DATA_DIR / "spark-warehouse"))
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8")
    )
    if jdbc_jar is not None:
        # 使用 extraClassPath 而不是 spark.jars：本地模式避免 Windows 触发
        # Hadoop winutils 的 chmod 依赖，同时 JDBC 驱动仍能被 JVM 加载
        jar_path = str(jdbc_jar.resolve())
        builder = builder.config("spark.driver.extraClassPath", jar_path).config(
            "spark.executor.extraClassPath", jar_path
        )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def export_behaviors_csv() -> Path:
    """JDBC 不可用时，用 PyMySQL 导出 CSV 给 Spark 读取。"""
    target = DATA_DIR / "behaviors.csv"
    db = settings.mysql
    conn = pymysql.connect(
        host=db["host"],
        port=db["port"],
        user=db["user"],
        password=db["password"],
        database=db["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, product_id, behavior_type, weight, created_at "
                "FROM user_behavior"
            )
            rows = cursor.fetchall()
        import csv

        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["id", "user_id", "product_id", "behavior_type", "weight", "created_at"]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["id"],
                        row["user_id"],
                        row["product_id"],
                        row["behavior_type"],
                        row["weight"],
                        row["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    ]
                )
    finally:
        conn.close()
    print(f"[ALS] 已导出行为数据 CSV：{target}（{len(rows)} 行）")
    return target


def load_behaviors(spark: SparkSession, jdbc_jar: Path | None) -> DataFrame:
    """优先 JDBC 读取 MySQL，失败时回退 CSV。"""
    if jdbc_jar is not None:
        print("[ALS] 通过 JDBC 读取 user_behavior ...")
        db = settings.mysql
        try:
            df = (
                spark.read.format("jdbc")
                .option("url", settings.jdbc_url)
                .option("dbtable", "user_behavior")
                .option("user", db["user"])
                .option("password", db["password"])
                .option("driver", JDBC_DRIVER_CLASS)
                .option("fetchsize", "1000")
                .load()
                .select("id", "user_id", "product_id", "behavior_type", "weight", "created_at")
            )
            df.count()
            return df
        except Exception as exc:
            print(f"[ALS] JDBC 读取失败，回退 CSV：{exc}")

    csv_path = export_behaviors_csv()
    print("[ALS] 通过 CSV 读取 user_behavior ...")
    return (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .option("encoding", "UTF-8")
        .csv(str(csv_path))
    )


def mysql_connection():
    """返回 PyMySQL 连接，用于读取商品销量 / 类目。"""
    db = settings.mysql
    return pymysql.connect(
        host=db["host"],
        port=db["port"],
        user=db["user"],
        password=db["password"],
        database=db["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def load_popular_products() -> list[int]:
    """按商品销量取热门 ID，用于补足推荐数量。"""
    conn = mysql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM product ORDER BY sales DESC, id ASC LIMIT 200"
            )
            return [int(row["id"]) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_redis_client() -> redis.Redis:
    """推荐任务使用的 Redis 客户端。"""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True, protocol=2)


def clear_keys(client: redis.Redis, patterns: list[str]) -> None:
    """按模式分批清理旧缓存。"""
    for pattern in patterns:
        batch: list[str] = []
        for key in client.scan_iter(match=pattern, count=500):
            batch.append(key)
            if len(batch) >= 500:
                client.delete(*batch)
                batch.clear()
        if batch:
            client.delete(*batch)


def item_similarities(model, top_n: int) -> dict[int, list[int]]:
    """用物品隐向量计算余弦相似度，取每个商品的 TopN。"""
    rows = model.itemFactors.select("id", "features").collect()
    ids = [int(row["id"]) for row in rows]
    # 不同 Spark / Arrow 配置下 features 可能是 DenseVector 或 list
    vectors = [
        row["features"].toArray()
        if hasattr(row["features"], "toArray")
        else list(row["features"])
        for row in rows
    ]
    matrix = np.asarray(vectors, dtype=np.float64)
    if matrix.size == 0:
        return {}

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized = matrix / norms
    scores = normalized @ normalized.T
    np.fill_diagonal(scores, -1.0)

    result: dict[int, list[int]] = {}
    k = min(top_n, max(len(ids) - 1, 0))
    if k <= 0:
        return result
    for row_index, product_id in enumerate(ids):
        candidates = np.argpartition(scores[row_index], -k)[-k:]
        candidates = candidates[np.argsort(scores[row_index][candidates])[::-1]]
        result[product_id] = [ids[int(idx)] for idx in candidates if ids[int(idx)] != product_id][:k]
    return result


def refresh_hot_zsets(client: redis.Redis) -> tuple[int, int]:
    """按商品销量刷新全局与类目热销 ZSET。"""
    conn = mysql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT p.id, p.sales, p.category_id, c.parent_id "
                "FROM product p JOIN category c ON c.id = p.category_id"
            )
            rows = cursor.fetchall()
    finally:
        conn.close()

    global_scores = {str(row["id"]): int(row["sales"]) for row in rows}
    category_scores: dict[int, dict[str, int]] = defaultdict(dict)
    for row in rows:
        score = int(row["sales"])
        category_scores[int(row["category_id"])][str(row["id"])] = score
        if row["parent_id"] is not None:
            category_scores[int(row["parent_id"])][str(row["id"])] = score

    clear_keys(client, ["hot:global", "hot:category:*"])
    pipe = client.pipeline()
    if global_scores:
        pipe.zadd("hot:global", global_scores)
    for category_id, mapping in category_scores.items():
        pipe.zadd(f"hot:category:{category_id}", mapping)
    pipe.execute()
    return len(global_scores), len(category_scores)


def train() -> None:
    """执行完整离线训练流程。"""
    started = time.perf_counter()
    jar = ensure_jdbc_jar()
    spark = build_spark("EcommerceALS", jar)
    try:
        behaviors = load_behaviors(spark, jar)
        behavior_count = behaviors.count()
        print(f"[ALS] 行为记录：{behavior_count} 条")
        if behavior_count == 0:
            raise RuntimeError("user_behavior 为空，请先执行 python -m app.data.seed")

        # 同一用户-商品的行为权重求和，作为隐式评分
        ratings = (
            behaviors.groupBy("user_id", "product_id")
            .agg(F.sum("weight").cast("float").alias("rating"))
            .cache()
        )
        rating_count = ratings.count()
        user_count = ratings.select("user_id").distinct().count()
        item_count = ratings.select("product_id").distinct().count()
        print(
            f"[ALS] 聚合评分：{rating_count} 条，用户 {user_count}，商品 {item_count}"
        )

        print(
            f"[ALS] 开始训练 ALS：rank={settings.rank}, "
            f"iterations={settings.iterations}, lambda={settings.reg_param}, "
            f"implicitPrefs={settings.implicit_prefs}, alpha={settings.alpha}"
        )
        # PySpark 4.0 已移除弃用的 ALS.train 类方法，Estimator.fit 与之等价：
        # rank / maxIter / regParam 分别对应规格中的 rank / iterations / lambda_
        als = ALS(
            rank=settings.rank,
            maxIter=settings.iterations,
            regParam=settings.reg_param,
            userCol="user_id",
            itemCol="product_id",
            ratingCol="rating",
            implicitPrefs=settings.implicit_prefs,
            alpha=settings.alpha,
            coldStartStrategy="drop",
            seed=42,
        )
        model = als.fit(ratings)

        # 读取训练集中已交互商品，推荐时过滤已看过/买过的商品
        seen: dict[int, set[int]] = defaultdict(set)
        for row in ratings.select("user_id", "product_id").collect():
            seen[int(row["user_id"])].add(int(row["product_id"]))

        popular_ids = load_popular_products()
        user_recs: dict[int, list[int]] = {}
        raw_recommendations = model.recommendForAllUsers(
            settings.user_top_n * 3
        ).collect()
        for row in raw_recommendations:
            user_id = int(row["user_id"])
            user_seen = seen[user_id]
            product_ids: list[int] = []
            for item in row["recommendations"]:
                product_id = int(item["product_id"])
                if product_id not in user_seen and product_id not in product_ids:
                    product_ids.append(product_id)
                if len(product_ids) >= settings.user_top_n:
                    break
            # 候选不足时用热销补齐
            if len(product_ids) < settings.user_top_n:
                for product_id in popular_ids:
                    if (
                        product_id not in user_seen
                        and product_id not in product_ids
                    ):
                        product_ids.append(product_id)
                    if len(product_ids) >= settings.user_top_n:
                        break
            user_recs[user_id] = product_ids[: settings.user_top_n]

        item_sims = item_similarities(model, settings.item_top_n)
        print(f"[ALS] 生成用户推荐 {len(user_recs)} 个，物品相似表 {len(item_sims)} 个")

        client = get_redis_client()
        client.ping()
        # 行为数据变化后同时清理共访缓存，避免 15 分钟内仍使用旧结果
        clear_keys(client, ["rec:user:*", "sim:item:*", "coview:item:*"])

        pipe = client.pipeline()
        for user_id, product_ids in user_recs.items():
            pipe.set(f"rec:user:{user_id}", json.dumps(product_ids))
        for product_id, similar_ids in item_sims.items():
            pipe.set(f"sim:item:{product_id}", json.dumps(similar_ids))
        pipe.execute()

        hot_product_count, hot_category_count = refresh_hot_zsets(client)
        elapsed = time.perf_counter() - started
        print(f"[ALS] 已写入 Redis：rec:user:*={len(user_recs)}，sim:item:*={len(item_sims)}")
        print(
            f"[ALS] 热销榜：hot:global={hot_product_count} 个商品，"
            f"hot:category:*={hot_category_count} 个类目"
        )
        print(f"[ALS] 训练完成，总耗时 {elapsed:.2f}s")
    finally:
        spark.stop()


if __name__ == "__main__":
    try:
        train()
    except Exception as exc:
        print(f"[ALS] 训练失败：{exc}", file=sys.stderr)
        raise
