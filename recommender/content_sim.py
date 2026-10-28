"""商品内容相似度：TF-IDF + 余弦相似度，用于新商品冷启动兜底。

运行：cd recommender && python content_sim.py
"""

from __future__ import annotations

import json
import time

import numpy as np
import pymysql
import redis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import settings


def load_products() -> list[dict]:
    """读取商品文本与类目名。"""
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
                "SELECT p.id, p.name, p.description, c.name AS category_name "
                "FROM product p JOIN category c ON c.id = p.category_id "
                "ORDER BY p.id"
            )
            return list(cursor.fetchall())
    finally:
        conn.close()


def clear_content_keys(client: redis.Redis) -> None:
    """清理旧的 rec:content:*。"""
    batch: list[str] = []
    for key in client.scan_iter(match="rec:content:*", count=500):
        batch.append(key)
        if len(batch) >= 500:
            client.delete(*batch)
            batch.clear()
    if batch:
        client.delete(*batch)


def build_content_similarity() -> None:
    """为每个商品生成 Top10 内容相似商品并写入 Redis。"""
    started = time.perf_counter()
    products = load_products()
    if not products:
        raise RuntimeError("商品表为空，请先执行 python -m app.data.seed")

    # 中文不做分词，使用字符 1-2gram，避免额外分词依赖
    texts = [
        f"{item['name']} {item['description']} {item['category_name']}"
        for item in products
    ]
    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(1, 2),
        min_df=1,
        max_features=30000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(texts)
    similarity = cosine_similarity(matrix)

    ids = [int(item["id"]) for item in products]
    result: dict[int, list[int]] = {}
    top_n = 10
    for row_index, product_id in enumerate(ids):
        row = similarity[row_index].copy()
        row[row_index] = -1.0
        count = min(top_n, len(ids) - 1)
        candidates = np.argpartition(row, -count)[-count:]
        candidates = candidates[np.argsort(row[candidates])[::-1]]
        result[product_id] = [ids[int(idx)] for idx in candidates if ids[int(idx)] != product_id]

    client = redis.Redis.from_url(settings.redis_url, decode_responses=True, protocol=2)
    client.ping()
    clear_content_keys(client)
    pipe = client.pipeline()
    for product_id, similar_ids in result.items():
        pipe.set(f"rec:content:{product_id}", json.dumps(similar_ids))
    pipe.execute()

    elapsed = time.perf_counter() - started
    print(
        f"[content_sim] 商品 {len(products)} 个，写入 rec:content:* {len(result)} 个，"
        f"耗时 {elapsed:.2f}s"
    )


if __name__ == "__main__":
    build_content_similarity()
