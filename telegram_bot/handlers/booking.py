from __future__ import annotations

from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from telegram_bot.keyboards.common import (
    booking_start_keyboard,
    dates_keyboard,
    group_poster_keyboard,
    slots_keyboard,
    tables_keyboard,
)
from telegram_bot.services.backend_client import BackendClient
from telegram_bot.settings import settings

router = Router()


class BookingState(StatesGroup):
    selecting_table = State()
    selecting_date = State()
    selecting_slot = State()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.text and "from_group" in message.text:
        await message.answer(
            "Вы пришли из группы. Давайте забронируем стол 👇",
            reply_markup=booking_start_keyboard(),
        )
        return
    await message.answer("Добро пожаловать!", reply_markup=booking_start_keyboard())


@router.callback_query(F.data == "start_booking")
async def start_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingState.selecting_table)
    tables = await BackendClient().get_tables()
    await callback.message.answer("Выберите стол:", reply_markup=tables_keyboard(tables))
    await callback.answer()


@router.callback_query(F.data.startswith("table:"))
async def select_table(callback: CallbackQuery, state: FSMContext) -> None:
    table_id = int(callback.data.split(":")[1])
    await state.update_data(table_id=table_id)
    await state.set_state(BookingState.selecting_date)
    await callback.message.answer("Выберите дату:", reply_markup=dates_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("date:"))
async def select_date(callback: CallbackQuery, state: FSMContext) -> None:
    choice = callback.data.split(":")[1]
    today = date.today()
    selected = today if choice == "today" else today + timedelta(days=1)
    await state.update_data(date=selected.isoformat())

    data = await state.get_data()
    slots = await BackendClient().get_availability(table_id=data["table_id"], date_value=selected)
    await state.set_state(BookingState.selecting_slot)
    await callback.message.answer("Выберите слот:", reply_markup=slots_keyboard(slots))
    await callback.answer()


@router.callback_query(F.data.startswith("slot:"))
async def select_slot(callback: CallbackQuery, state: FSMContext) -> None:
    _, time_range = callback.data.split(":", 1)
    start_str, end_str = time_range.split("|")
    data = await state.get_data()

    payload = {
        "table_id": data["table_id"],
        "start_at": start_str,
        "end_at": end_str,
        "tg_user_id": callback.from_user.id,
        "name": callback.from_user.full_name,
    }
    response = await BackendClient().create_hold(payload)
    await callback.message.answer(
        f"Бронь создана. Перейдите к оплате: {response.get('paymentUrl')}"
    )
    await state.clear()
    await callback.answer()


@router.message(Command("mybookings"))
async def my_bookings(message: Message) -> None:
    bookings = await BackendClient().list_bookings(message.from_user.id)
    if not bookings:
        await message.answer("Активных броней нет.")
        return
    lines = [f"#{item['id']} {item['start_at']} - {item['end_at']} ({item['status']})" for item in bookings]
    await message.answer("\n".join(lines))


@router.message(Command("cancel"))
async def cancel_booking(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /cancel <booking_id>")
        return
    booking_id = int(parts[1])
    response = await BackendClient().cancel_booking(booking_id)
    await message.answer(f"Статус брони: {response.get('status')}")


@router.message(Command("post_booking"))
async def post_booking(message: Message) -> None:
    if message.chat.type not in {"group", "supergroup"}:
        await message.answer("Команда доступна только в группах.")
        return
    admin_ids = {
        int(value)
        for value in (settings.admin_tg_ids or "").split(",")
        if value.strip()
    }
    if admin_ids and message.from_user.id not in admin_ids:
        await message.answer("Нет доступа")
        return
    bot_username = settings.telegram_bot_username or "<bot_username>"
    text = "📦 Аренда столов для упаковки. Нажмите кнопку ниже, чтобы забронировать время."
    await message.answer(text, reply_markup=group_poster_keyboard(bot_username))


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()
