"""商品分类模型，支持父子层级。"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    """商品分类，parent_id 为空表示一级分类。"""

    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True
    )

    parent = relationship(
        "Category", remote_side=[id], back_populates="children", lazy="joined"
    )
    children = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )
    products = relationship("Product", back_populates="category")
