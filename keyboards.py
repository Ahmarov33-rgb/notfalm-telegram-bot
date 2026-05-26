from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from config import settings
from typing import List, Dict


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=settings.MINI_APP_URL))],
        [KeyboardButton(text="📦 Каталог"), KeyboardButton(text="🛒 Мои заказы")],
        [KeyboardButton(text="💬 Поддержка"), KeyboardButton(text="⭐ Отзывы")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        emoji = cat.get("emoji", "📦")
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {cat['name']}",
            callback_data=f"cat_{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products: List[Dict], category_id: int = None) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        stock = p.get("stock_count", 0)
        status = "✅" if stock > 0 else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {p['name']} — {p['price']}₽",
            callback_data=f"prod_{p['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(product_id: int, in_stock: bool) -> InlineKeyboardMarkup:
    buttons = []
    if in_stock:
        buttons.append([InlineKeyboardButton(
            text="🛒 Купить", callback_data=f"buy_{product_id}"
        )])
    else:
        buttons.append([InlineKeyboardButton(text="❌ Нет в наличии", callback_data="no_stock")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_products")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_order_{order_id}")]
    ])


def admin_order_keyboard(order_id: int, user_tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{order_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"admin_cancel_{order_id}")
        ]
    ])


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [
            InlineKeyboardButton(text="📂 Категории", callback_data="admin_categories"),
            InlineKeyboardButton(text="📦 Товары", callback_data="admin_products")
        ],
        [
            InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders"),
            InlineKeyboardButton(text="💬 Тикеты", callback_data="admin_tickets")
        ],
        [InlineKeyboardButton(text="🔙 Закрыть", callback_data="admin_close")]
    ])


def orders_list_keyboard(orders: List[Dict], status_filter: str = None) -> InlineKeyboardMarkup:
    buttons = []
    for o in orders[:10]:
        status_emoji = {"pending": "🕐", "awaiting_payment": "⏳", "paid": "💰",
                        "completed": "✅", "cancelled": "❌"}.get(o["status"], "❓")
        buttons.append([InlineKeyboardButton(
            text=f"{status_emoji} #{o['id']} — {o['total_amount']}₽",
            callback_data=f"admin_order_{o['id']}"
        )])

    filter_buttons = [
        InlineKeyboardButton(text="💰 Ждут подтверждения", callback_data="admin_orders_paid"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    ]
    buttons.append(filter_buttons)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
