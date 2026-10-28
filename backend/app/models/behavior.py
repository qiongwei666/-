"""用户行为模型，推荐系统的主要数据源。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 行为类型 -> 隐式评分权重
BEHAVIOR_WEIGHTS: dict[str, int] = {
    "view": 1,
    "click": 2,
    "cart": 3,
    "buy": 5,
}


class UserBehavior(Base):
    """用户行为流水。"""

    __tablename__ = "user_behavior"
    __table_args__ = (
        Index("idx_user_time", "user_id", "created_at"),
        Index("idx_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    # view / click / cart / buy
    behavior_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # view=1, click=2, cart=3, buy=5
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    user = relationship("User", back_populates="behaviors")
    product = relationship("Product", back_populates="behaviors")
