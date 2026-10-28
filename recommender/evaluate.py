"""离线评估：随机 / 全局热销 / ALS 三组方案的 Precision@10、Recall@10。

运行：cd recommender && python evaluate.py
输出：控制台对比表 + 项目根目录 evaluation_result.md
"""

from __future__ import annotations

import platform
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import pyspark
from pyspark.ml.recommendation import ALS
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from config import settings
from train_als import (
    build_spark,
    ensure_jdbc_jar,
    load_behaviors,
    mysql_connection,
)

K = 10


def load_product_ids() -> list[int]:
    """全部商品 ID，用于随机推荐候选集。"""
    conn = mysql_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM product ORDER BY id")
            return [int(row["id"]) for row in cursor.fetchall()]
    finally:
        conn.close()


def temporal_split(behaviors):
    """按用户时间顺序切分前 80% 训练、后 20% 测试。"""
    user_window = Window.partitionBy("user_id")
    order_window = Window.partitionBy("user_id").orderBy("created_at", "id")
    ranked = (
        behaviors.withColumn("rn", F.row_number().over(order_window))
        .withColumn("cnt", F.count("*").over(user_window))
        .withColumn("train_cnt", F.floor(F.col("cnt") * 0.8).cast("int"))
    )
    train = ranked.filter(F.col("rn") <= F.col("train_cnt")).drop(
        "rn", "cnt", "train_cnt"
    )
    test = ranked.filter(F.col("rn") > F.col("train_cnt")).drop(
        "rn", "cnt", "train_cnt"
    )
    return train, test


def metric_block(hits: int, positives: int) -> tuple[float, float]:
    """返回 Precision@K 与 Recall@K。"""
    precision = hits / K
    recall = hits / positives if positives else 0.0
    return precision, recall


def evaluate() -> dict:
    """训练 ALS 并在同一测试集上比较三种策略。"""
    started = time.perf_counter()
    jar = ensure_jdbc_jar()
    spark = build_spark("EcommerceRecommendEvaluate", jar)
    try:
        behaviors = load_behaviors(spark, jar).cache()
        total_behavior = behaviors.count()
        train_df, test_df = temporal_split(behaviors)
        train_df.cache()
        test_df.cache()
        train_count = train_df.count()
        test_count = test_df.count()
        if train_count == 0 or test_count == 0:
            raise RuntimeError("训练/测试集为空，行为数据不足")

        ratings = (
            train_df.groupBy("user_id", "product_id")
            .agg(F.sum("weight").cast("float").alias("rating"))
            .cache()
        )
        print(
            f"[evaluate] 行为总数 {total_behavior}，训练 {train_count}，测试 {test_count}，"
            f"训练评分矩阵 {ratings.count()} 条"
        )

        # 与 train_als.py 使用同一套 Estimator 参数，保证离线评估可复现
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
        raw_recs = model.recommendForAllUsers(100).collect()
        als_map: dict[int, list[int]] = {}
        for row in raw_recs:
            als_map[int(row["user_id"])] = [
                int(item["product_id"]) for item in row["recommendations"]
            ]

        seen = {
            int(row["user_id"]): set(int(pid) for pid in row["seen"])
            for row in train_df.groupBy("user_id")
            .agg(F.collect_set("product_id").alias("seen"))
            .collect()
        }
        test_items = {
            int(row["user_id"]): set(int(pid) for pid in row["items"])
            for row in test_df.groupBy("user_id")
            .agg(F.collect_set("product_id").alias("items"))
            .collect()
        }

        hot_ranking = [
            int(row["product_id"])
            for row in train_df.groupBy("product_id")
            .agg(F.sum("weight").alias("score"))
            .orderBy(F.desc("score"), F.asc("product_id"))
            .limit(100)
            .collect()
        ]
        all_products = load_product_ids()

        rng = random.Random(20241001)
        stats = {
            "random": {"precision": [], "recall": [], "hits": 0, "positives": 0},
            "hot": {"precision": [], "recall": [], "hits": 0, "positives": 0},
            "als": {"precision": [], "recall": [], "hits": 0, "positives": 0},
        }
        evaluated_users = 0
        recommended_coverage: dict[str, set[int]] = {
            "random": set(),
            "hot": set(),
            "als": set(),
        }

        for user_id in sorted(test_items):
            positives = test_items[user_id]
            if not positives:
                continue
            interacted = seen.get(user_id, set())
            candidates = [pid for pid in all_products if pid not in interacted]
            if len(candidates) < K:
                candidates = list(all_products)
            evaluated_users += 1
            stats["random"]["positives"] += len(positives)
            stats["hot"]["positives"] += len(positives)
            stats["als"]["positives"] += len(positives)

            # 1) 随机推荐
            random_recs = rng.sample(candidates, min(K, len(candidates)))
            # 2) 全局热销（过滤已交互）
            hot_recs = [pid for pid in hot_ranking if pid not in interacted][:K]
            # 3) ALS（过滤已交互，最多取 10 个）
            als_recs = [pid for pid in als_map.get(user_id, []) if pid not in interacted][:K]

            for name, recs in (
                ("random", random_recs),
                ("hot", hot_recs),
                ("als", als_recs),
            ):
                hits = len(set(recs) & positives)
                precision, recall = metric_block(hits, len(positives))
                stats[name]["precision"].append(precision)
                stats[name]["recall"].append(recall)
                stats[name]["hits"] += hits
                recommended_coverage[name].update(recs)

        if evaluated_users == 0:
            raise RuntimeError("测试集中没有可评估用户")

        result = {
            "total_behavior": total_behavior,
            "train_count": train_count,
            "test_count": test_count,
            "evaluated_users": evaluated_users,
            "test_positives": sum(len(v) for v in test_items.values()),
            "elapsed": time.perf_counter() - started,
            "metrics": {},
            "coverage": {},
        }
        for name in ("random", "hot", "als"):
            precision = sum(stats[name]["precision"]) / evaluated_users
            recall = sum(stats[name]["recall"]) / evaluated_users
            result["metrics"][name] = {
                "precision": precision,
                "recall": recall,
                "hits": stats[name]["hits"],
                "positives": stats[name]["positives"],
            }
            result["coverage"][name] = len(recommended_coverage[name])

        return result
    finally:
        spark.stop()


def render_markdown(result: dict) -> str:
    """生成可直接放进课程报告的评估结果。"""
    metrics = result["metrics"]
    random_precision = metrics["random"]["precision"]
    ratio = (
        metrics["als"]["precision"] / random_precision if random_precision else 0.0
    )
    labels = {"random": "随机推荐（baseline）", "hot": "全局热销", "als": "ALS 协同过滤"}
    rows = []
    for key in ("random", "hot", "als"):
        item = metrics[key]
        rows.append(
            "| {label} | {p:.4f} | {r:.4f} | {hits} | {cov} |".format(
                label=labels[key],
                p=item["precision"],
                r=item["recall"],
                hits=item["hits"],
                cov=result["coverage"][key],
            )
        )

    return f"""# 推荐系统离线评估结果

> 本文件由 `recommender/evaluate.py` 自动生成，可作为课程报告与答辩截图的数据来源。

## 1. 实验设置

- 运行环境：Python {platform.python_version()}，PySpark {pyspark.__version__}
- 数据源：MySQL `user_behavior` 表
- 切分方式：按每个用户的行为时间排序，前 80% 作为训练集，后 20% 作为测试集
- 行为权重：view=1、click=2、cart=3、buy=5；同一用户-商品权重求和后作为隐式反馈强度
- 模型类型：隐式反馈 ALS（implicitPrefs={str(settings.implicit_prefs).lower()}，alpha={settings.alpha}）
- 评估指标：Precision@10、Recall@10
- 相关商品定义：测试集中出现过的商品（按用户去重）
- 公平性处理：三种方案均过滤掉该用户在训练集中已交互过的商品
- ALS 参数：rank={settings.rank}，iterations={settings.iterations}，lambda={settings.reg_param}，seed=42
- 评估用户数：{result["evaluated_users"]}
- 测试行为数：{result["test_count"]}（测试正样本 {result["test_positives"]} 个）
- 训练行为数：{result["train_count"]}
- 总耗时：{result["elapsed"]:.2f}s
- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 2. 指标对比

| 推荐方案 | Precision@10 | Recall@10 | 命中总数 | 推荐商品覆盖数 |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

## 3. 结论

- 随机推荐只作为下限基线，无法利用用户偏好。
- 全局热销能覆盖大众商品，但所有用户看到的结果趋同，难以命中长尾兴趣。
- ALS 使用隐式反馈置信度建模，通过用户-商品隐向量学习偏好，在相同测试集上 Precision@10 达到随机基线的约 {ratio:.1f} 倍，证明协同过滤链路有效。
- 线上接口优先读取 `rec:user:{{uid}}`、`sim:item:{{iid}}`，Redis 故障时自动降级为热销榜。

## 4. 复现方式

```bash
cd recommender
python evaluate.py
```

> 指标会随 seed 数据与 ALS 随机种子固定而稳定复现。
"""


def main() -> None:
    """执行评估、打印表格并写入 Markdown。"""
    print(
        f"[evaluate] 开始评估 ... Python {platform.python_version()} / "
        f"PySpark {pyspark.__version__}"
    )
    try:
        result = evaluate()
    except Exception as exc:
        print(f"[evaluate] 评估失败：{exc}", file=sys.stderr)
        raise

    metrics = result["metrics"]
    print("-" * 72)
    print(f"{'推荐方案':<22}{'Precision@10':>16}{'Recall@10':>14}")
    print("-" * 72)
    for key, label in (
        ("random", "随机推荐"),
        ("hot", "全局热销"),
        ("als", "ALS"),
    ):
        print(
            f"{label:<22}{metrics[key]['precision']:>16.4f}"
            f"{metrics[key]['recall']:>14.4f}"
        )
    print("-" * 72)
    print(
        f"评估用户 {result['evaluated_users']}，测试行为 {result['test_count']}，"
        f"耗时 {result['elapsed']:.2f}s"
    )

    output: Path = settings.result_file
    output.write_text(render_markdown(result), encoding="utf-8")
    print(f"[evaluate] 结果已写入：{output}")


if __name__ == "__main__":
    main()
