"""订单与订单明细模型。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    """订单主表。作业项目采用“下单即支付成功”的简化流程。"""

    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="paid", index=True
    )
    tracking_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    return_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    return_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False, index=True
    )

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def total_quantity(self) -> int:
        """订单商品总件数。"""
        return sum(item.quantity for item in self.items)

    @property
    def username(self) -> str:
        """下单用户名，供后台订单列表展示。"""
        return self.user.username if self.user else ""


class OrderItem(Base):
    """订单明细，保存下单时的成交价快照。"""

    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items", lazy="joined")

    @property
    def subtotal(self) -> Decimal:
        """明细小计。"""
        return self.price * self.quantity

    @property
    def product_name(self) -> str:
        """商品名称快照（当前取商品表）。"""
        return self.product.name if self.product else ""

    @property
    def image_url(self) -> str:
        """商品图片。"""
        return self.product.image_url if self.product else ""
