from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from api_client import api
from keyboards import admin_panel_keyboard, orders_list_keyboard, admin_order_keyboard
from config import settings

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


# ── FSM States ─────────────────────────────────────────────────────────────────
class AdminStates(StatesGroup):
    # Category
    waiting_category_name = State()
    waiting_category_emoji = State()
    # Product
    waiting_product_name = State()
    waiting_product_price = State()
    waiting_product_description = State()
    waiting_product_category = State()
    waiting_product_image = State()
    # Digital items
    waiting_product_id_for_items = State()
    waiting_digital_items = State()
    # Support reply
    waiting_support_reply = State()
    # Edit product
    waiting_edit_product_id = State()
    waiting_edit_field = State()
    waiting_edit_value = State()


# ── Admin Entry ────────────────────────────────────────────────────────────────
@router.message(F.text == "⚙️ Админ-панель")
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⚙️ <b>Админ-панель NOTFALM SHOP</b>",
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "⚙️ <b>Админ-панель NOTFALM SHOP</b>",
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


# ── Stats ──────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    stats = await api.get_stats(callback.from_user.id)
    text = (
        f"📊 <b>Статистика магазина</b>\n\n"
        f"👥 Пользователей: <b>{stats.get('total_users', 0)}</b>\n"
        f"📦 Товаров: <b>{stats.get('total_products', 0)}</b>\n"
        f"📋 Заказов всего: <b>{stats.get('total_orders', 0)}</b>\n"
        f"💰 Ожидают подтверждения: <b>{stats.get('pending_orders', 0)}</b>\n"
        f"✅ Выполнено заказов: <b>{stats.get('completed_orders', 0)}</b>\n"
        f"💵 Выручка: <b>{stats.get('total_revenue', 0):.2f}₽</b>\n"
        f"💬 Открытых тикетов: <b>{stats.get('open_tickets', 0)}</b>"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()


# ── Categories ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    categories = await api.get_categories()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = [[InlineKeyboardButton(
        text=f"{c.get('emoji', '📦')} {c['name']}",
        callback_data=f"admin_del_cat_{c['id']}"
    )] for c in categories]
    buttons.append([InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_add_category")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])

    await callback.message.edit_text(
        "📂 <b>Категории</b>\nНажми на категорию чтобы удалить:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_category_name)
    await callback.message.answer("Введи название новой категории:")
    await callback.answer()


@router.message(AdminStates.waiting_category_name)
async def add_category_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminStates.waiting_category_emoji)
    await message.answer("Введи эмодзи для категории (или отправь - для пропуска):")


@router.message(AdminStates.waiting_category_emoji)
async def add_category_emoji(message: Message, state: FSMContext):
    data = await state.get_data()
    emoji = message.text if message.text != "-" else "📦"
    name = data["name"]
    slug = name.lower().replace(" ", "-").replace("_", "-")

    result = await api.create_category(message.from_user.id, name, slug, emoji)
    await state.clear()

    if "id" in result:
        await message.answer(f"✅ Категория <b>{name}</b> создана!", parse_mode="HTML")
    else:
        await message.answer(f"❌ Ошибка: {result.get('detail', 'Неизвестная ошибка')}")


@router.callback_query(F.data.startswith("admin_del_cat_"))
async def delete_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cat_id = int(callback.data.split("_")[-1])
    result = await api.delete_category(callback.from_user.id, cat_id)
    if result.get("ok"):
        await callback.answer("✅ Категория удалена", show_alert=True)
        # Refresh
        await admin_categories(callback)
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)


# ── Products ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    products = await api.get_products()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = []
    for p in products[:15]:
        stock = p.get("stock_count", 0)
        buttons.append([InlineKeyboardButton(
            text=f"{'✅' if p['is_active'] else '🔴'} {p['name']} [{stock} шт.]",
            callback_data=f"admin_prod_{p['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")])
    buttons.append([InlineKeyboardButton(text="📥 Загрузить товары", callback_data="admin_upload_items")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])

    await callback.message.edit_text(
        "📦 <b>Товары магазина</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_product_name)
    await callback.message.answer("Введи название товара:")
    await callback.answer()


@router.message(AdminStates.waiting_product_name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer("Введи цену (только число, например: 299):")


@router.message(AdminStates.waiting_product_price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи корректную цену (число):")
        return
    await state.update_data(price=price)
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer("Введи описание товара (или - для пропуска):")


@router.message(AdminStates.waiting_product_description)
async def add_product_desc(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else None
    await state.update_data(description=desc)
    await state.set_state(AdminStates.waiting_product_category)

    categories = await api.get_categories()
    cats_text = "\n".join([f"{c['id']}. {c['name']}" for c in categories])
    await message.answer(
        f"Введи ID категории (или 0 для пропуска):\n\n{cats_text or 'Категорий нет'}"
    )


@router.message(AdminStates.waiting_product_category)
async def add_product_category(message: Message, state: FSMContext):
    try:
        cat_id = int(message.text)
    except ValueError:
        cat_id = 0
    await state.update_data(category_id=cat_id if cat_id > 0 else None)
    await state.set_state(AdminStates.waiting_product_image)
    await message.answer("Введи URL изображения товара (или - для пропуска):")


@router.message(AdminStates.waiting_product_image)
async def add_product_image(message: Message, state: FSMContext):
    image_url = message.text if message.text != "-" else None
    data = await state.get_data()
    data["image_url"] = image_url

    result = await api.create_product(message.from_user.id, data)
    await state.clear()

    if "id" in result:
        await message.answer(
            f"✅ Товар <b>{result['name']}</b> создан!\n"
            f"ID: {result['id']}\n"
            f"Теперь загрузи цифровые товары: нажми «Загрузить товары» в панели",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"❌ Ошибка: {result.get('detail', 'Неизвестная ошибка')}")


@router.callback_query(F.data.startswith("admin_prod_"))
async def admin_product_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[-1])
    product = await api.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    stock = await api.get_stock(product_id)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    status = "✅ Активен" if product["is_active"] else "🔴 Отключён"
    toggle_text = "🔴 Отключить" if product["is_active"] else "✅ Включить"

    await callback.message.edit_text(
        f"📦 <b>{product['name']}</b>\n\n"
        f"💰 Цена: {product['price']}₽\n"
        f"📊 Статус: {status}\n"
        f"🗂 Остаток: {stock} шт.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_toggle_{product_id}_{product['is_active']}")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"admin_price_{product_id}")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"admin_del_prod_{product_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_products")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_"))
async def toggle_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    product_id = int(parts[2])
    current = parts[3] == "True"
    result = await api.update_product(callback.from_user.id, product_id, {"is_active": not current})
    if "id" in result:
        status = "включён" if not current else "отключён"
        await callback.answer(f"✅ Товар {status}", show_alert=True)
        await admin_product_detail(callback)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_del_prod_"))
async def delete_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[-1])
    result = await api.delete_product(callback.from_user.id, product_id)
    if result.get("ok"):
        await callback.answer("✅ Товар удалён", show_alert=True)
        await admin_products(callback)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


# ── Upload Digital Items ────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_upload_items")
async def upload_items_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_product_id_for_items)
    await callback.message.answer(
        "📥 Введи <b>ID товара</b> для загрузки цифровых позиций:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_product_id_for_items)
async def upload_items_product_id(message: Message, state: FSMContext):
    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer("❌ Введи числовой ID товара:")
        return

    product = await api.get_product(product_id)
    if not product:
        await message.answer("❌ Товар не найден. Введи другой ID:")
        return

    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_digital_items)
    await message.answer(
        f"✅ Товар: <b>{product['name']}</b>\n\n"
        f"Теперь отправь цифровые позиции — <b>каждая с новой строки</b>:\n\n"
        f"Пример:\n<code>KEY-XXXX-YYYY-ZZZZ\nKEY-AAAA-BBBB-CCCC</code>",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_digital_items)
async def upload_items_content(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]

    contents = [line.strip() for line in message.text.split("\n") if line.strip()]
    if not contents:
        await message.answer("❌ Список пустой. Попробуй ещё раз:")
        return

    result = await api.bulk_add_digital_items(message.from_user.id, product_id, contents)
    await state.clear()

    added = result.get("added", 0)
    await message.answer(f"✅ Загружено <b>{added}</b> позиций!", parse_mode="HTML")


# ── Orders ─────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    orders = await api.get_orders(callback.from_user.id)
    await callback.message.edit_text(
        "📋 <b>Последние заказы</b>",
        parse_mode="HTML",
        reply_markup=orders_list_keyboard(orders)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_orders_paid")
async def admin_orders_paid(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    orders = await api.get_orders(callback.from_user.id, status="paid")
    if not orders:
        await callback.answer("Нет заказов ожидающих подтверждения", show_alert=True)
        return

    await callback.message.edit_text(
        "💰 <b>Ожидают подтверждения оплаты:</b>",
        parse_mode="HTML",
        reply_markup=orders_list_keyboard(orders)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_"))
async def admin_order_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    order_id = int(callback.data.split("_")[-1])

    import httpx
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{settings.API_URL}/api/orders/{order_id}",
            headers={"x-admin-id": str(callback.from_user.id)}
        )

    if r.status_code != 200:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    order = r.json()
    user = order.get("user", {})
    username = f"@{user.get('username')}" if user.get("username") else user.get("telegram_id", "?")

    status_map = {"pending": "🕐", "awaiting_payment": "⏳", "paid": "💰", "completed": "✅", "cancelled": "❌"}
    status = status_map.get(order["status"], "❓") + " " + order["status"]

    items_text = ""
    for item in order.get("items", []):
        prod = item.get("product", {})
        items_text += f"  • {prod.get('name', '?')} x{item['quantity']} — {item['price']}₽\n"

    text = (
        f"📋 <b>Заказ #{order['id']}</b>\n\n"
        f"👤 Покупатель: {username}\n"
        f"📦 Товары:\n{items_text}"
        f"💰 Сумма: <b>{order['total_amount']}₽</b>\n"
        f"🔹 Статус: {status}"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"admin_confirm_{order_id}"),
        ],
        [InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"admin_cancel_{order_id}")],
        [InlineKeyboardButton(text="🔙 К заказам", callback_data="admin_orders")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_order(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    order_id = int(callback.data.split("_")[-1])

    result = await api.confirm_order(order_id, callback.from_user.id)

    if not result.get("ok"):
        await callback.answer(f"❌ {result.get('detail', 'Ошибка')}", show_alert=True)
        return

    # Send items to buyer
    user_tg_id = result.get("user_telegram_id")
    delivered = result.get("delivered_items", [])

    if user_tg_id and delivered:
        items_text = "\n".join([f"🔑 <code>{item['content']}</code>" for item in delivered])
        try:
            await bot.send_message(
                user_tg_id,
                f"✅ <b>Оплата подтверждена!</b>\n\n"
                f"Заказ #{order_id} выполнен. Твои товары:\n\n"
                f"{items_text}\n\n"
                f"Спасибо за покупку в NOTFALM SHOP! 🛍",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await callback.answer("✅ Заказ подтверждён, товар отправлен!", show_alert=True)
    await callback.message.edit_text(
        f"✅ <b>Заказ #{order_id} подтверждён!</b>\nТовар отправлен покупателю.",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel_order(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    order_id = int(callback.data.split("_")[-1])

    result = await api.cancel_order(order_id, callback.from_user.id)
    if result.get("ok"):
        await callback.answer("✅ Заказ отменён", show_alert=True)
        await callback.message.edit_text(f"❌ <b>Заказ #{order_id} отменён.</b>", parse_mode="HTML")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


# ── Support tickets ────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    tickets = await api.get_support_tickets(callback.from_user.id)
    open_tickets = [t for t in tickets if t["status"] == "open"]

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for t in open_tickets[:10]:
        user = t.get("user", {})
        name = user.get("username") or user.get("first_name") or str(user.get("telegram_id", "?"))
        buttons.append([InlineKeyboardButton(
            text=f"#{t['id']} @{name}: {t['subject'][:30]}",
            callback_data=f"admin_ticket_{t['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])

    count = len(open_tickets)
    await callback.message.edit_text(
        f"💬 <b>Открытые тикеты ({count})</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ticket_"))
async def admin_ticket_detail(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    ticket_id = int(callback.data.split("_")[-1])

    import httpx
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{settings.API_URL}/api/support/",
            headers={"x-admin-id": str(callback.from_user.id)}
        )
    tickets = r.json()
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)

    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return

    user = ticket.get("user", {})
    username = f"@{user.get('username')}" if user.get("username") else str(user.get("telegram_id", "?"))

    await state.update_data(reply_ticket_id=ticket_id, reply_user_tg=user.get("telegram_id"))
    await state.set_state(AdminStates.waiting_support_reply)

    await callback.message.answer(
        f"💬 <b>Тикет #{ticket_id}</b>\n"
        f"От: {username}\n\n"
        f"<b>Тема:</b> {ticket['subject']}\n"
        f"<b>Сообщение:</b>\n{ticket['message']}\n\n"
        f"Введи ответ:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_support_reply)
async def send_support_reply(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    user_tg = data.get("reply_user_tg")

    await api.reply_ticket(message.from_user.id, ticket_id, message.text)
    await state.clear()

    # Notify user
    if user_tg:
        try:
            await bot.send_message(
                user_tg,
                f"💬 <b>Ответ на ваш тикет #{ticket_id}:</b>\n\n{message.text}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await message.answer(f"✅ Ответ на тикет #{ticket_id} отправлен!")
