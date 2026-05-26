from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from api_client import api
from keyboards import main_menu_keyboard, categories_keyboard, products_keyboard, product_detail_keyboard
from config import settings

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await api.upsert_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    admin = is_admin(user.id)
    name = user.first_name or "друг"

    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"🛍 Добро пожаловать в <b>NOTFALM SHOP</b>\n\n"
        f"Здесь ты можешь купить цифровые товары быстро и безопасно.\n\n"
        f"Нажми <b>«Открыть магазин»</b> для полного опыта или используй меню ниже 👇",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(admin)
    )


@router.message(F.text == "📦 Каталог")
async def show_catalog(message: Message):
    categories = await api.get_categories()
    if not categories:
        await message.answer("😔 Каталог пуст. Загляни позже!")
        return

    await message.answer(
        "📂 <b>Выберите категорию:</b>",
        parse_mode="HTML",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith("cat_"))
async def show_category_products(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[1])
    products = await api.get_products(category_id=category_id)

    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return

    await callback.message.edit_text(
        "📦 <b>Товары в категории:</b>",
        parse_mode="HTML",
        reply_markup=products_keyboard(products, category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = await api.get_product(product_id)

    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    stock = product.get("stock_count", 0)
    stock_text = f"✅ В наличии: {stock} шт." if stock > 0 else "❌ Нет в наличии"

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"{product.get('description', 'Описание не указано')}\n\n"
        f"💰 Цена: <b>{product['price']}₽</b>\n"
        f"{stock_text}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=product_detail_keyboard(product_id, stock > 0)
    )
    await callback.answer()


@router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery):
    categories = await api.get_categories()
    await callback.message.edit_text(
        "📂 <b>Выберите категорию:</b>",
        parse_mode="HTML",
        reply_markup=categories_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "no_stock")
async def no_stock_alert(callback: CallbackQuery):
    await callback.answer("❌ Товар закончился", show_alert=True)


@router.message(F.text == "🛒 Мои заказы")
async def show_my_orders(message: Message):
    orders = await api.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer("📭 У тебя пока нет заказов.")
        return

    status_map = {
        "pending": "🕐 Создан",
        "awaiting_payment": "⏳ Ожидает оплаты",
        "paid": "💰 Оплачен (проверяем)",
        "completed": "✅ Выполнен",
        "cancelled": "❌ Отменён"
    }

    text = "📋 <b>Твои заказы:</b>\n\n"
    for order in orders[:10]:
        status = status_map.get(order["status"], order["status"])
        text += f"<b>Заказ #{order['id']}</b> — {order['total_amount']}₽\n"
        text += f"Статус: {status}\n"

        if order["status"] == "completed" and order.get("items"):
            for item in order["items"]:
                if item.get("digital_item"):
                    text += f"🔑 <code>{item['digital_item']['content']}</code>\n"
        text += "\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💬 Поддержка")
async def show_support(message: Message):
    await message.answer(
        "💬 <b>Поддержка NOTFALM SHOP</b>\n\n"
        "Напиши нам своё сообщение в формате:\n"
        "<code>/support Ваш вопрос или проблема</code>\n\n"
        "Мы ответим как можно скорее! ⚡",
        parse_mode="HTML"
    )


@router.message(Command("support"))
async def create_support_ticket(message: Message):
    text = message.text.replace("/support", "").strip()
    if not text:
        await message.answer("Напиши вопрос после команды: /support Ваш вопрос")
        return

    try:
        async with __import__("httpx").AsyncClient() as client:
            r = await client.post(
                f"{settings.API_URL}/api/support/",
                json={
                    "telegram_id": message.from_user.id,
                    "subject": text[:100],
                    "message": text
                }
            )
        if r.status_code == 200:
            await message.answer("✅ Тикет создан! Мы ответим тебе здесь в боте.")
        else:
            await message.answer("❌ Ошибка. Попробуй позже.")
    except Exception:
        await message.answer("❌ Ошибка соединения. Попробуй позже.")


@router.message(F.text == "⭐ Отзывы")
async def show_reviews_info(message: Message):
    await message.answer(
        "⭐ <b>Отзывы покупателей</b>\n\n"
        "Чтобы оставить отзыв, используй Mini App магазина.\n\n"
        "👇 Нажми <b>«Открыть магазин»</b> → страница товара → Оставить отзыв",
        parse_mode="HTML"
    )
