from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
import httpx

from api_client import api
from keyboards import order_confirm_keyboard
from config import settings

router = Router()


@router.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery, bot: Bot):
    product_id = int(callback.data.split("_")[1])
    product = await api.get_product(product_id)

    if not product or product.get("stock_count", 0) == 0:
        await callback.answer("❌ Товар недоступен", show_alert=True)
        return

    # Create order via API
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{settings.API_URL}/api/orders/",
                json={
                    "telegram_id": callback.from_user.id,
                    "items": [{"product_id": product_id, "quantity": 1}]
                }
            )
        if r.status_code != 200:
            error = r.json().get("detail", "Ошибка создания заказа")
            await callback.answer(f"❌ {error}", show_alert=True)
            return

        order = r.json()
        payment_details = order.get("payment_details", settings.PAYMENT_DETAILS)

        text = (
            f"🛒 <b>Заказ #{order['id']} создан!</b>\n\n"
            f"Товар: <b>{product['name']}</b>\n"
            f"Сумма: <b>{order['total_amount']}₽</b>\n\n"
            f"💳 <b>Реквизиты для оплаты:</b>\n"
            f"<code>{payment_details}</code>\n\n"
            f"После оплаты нажми кнопку ниже 👇"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=order_confirm_keyboard(order["id"])
        )

    except Exception as e:
        await callback.answer("❌ Ошибка соединения", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("paid_"))
async def confirm_payment(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split("_")[1])

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{settings.API_URL}/api/orders/{order_id}/paid")

        if r.status_code != 200:
            await callback.answer("❌ Ошибка", show_alert=True)
            return

        # Notify all admins
        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(
                    admin_id,
                    f"💰 <b>Новая оплата!</b>\n\n"
                    f"Заказ: <b>#{order_id}</b>\n"
                    f"Покупатель: @{callback.from_user.username or callback.from_user.id}\n"
                    f"Telegram ID: <code>{callback.from_user.id}</code>\n\n"
                    f"Нажми /admin чтобы подтвердить",
                    parse_mode="HTML"
                )
            except Exception:
                pass

        await callback.message.edit_text(
            f"⏳ <b>Заявка принята!</b>\n\n"
            f"Заказ #{order_id} передан на проверку.\n"
            f"После подтверждения оплаты ты получишь свой товар здесь. ⚡",
            parse_mode="HTML"
        )

    except Exception:
        await callback.answer("❌ Ошибка соединения", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_user(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        f"❌ Заказ #{order_id} отменён.",
        parse_mode="HTML"
    )
    await callback.answer()
