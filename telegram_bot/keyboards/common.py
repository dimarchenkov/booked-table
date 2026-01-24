from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def booking_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Забронировать", callback_data="start_booking")]]
    )


def tables_keyboard(tables: list[dict]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=table["name"], callback_data=f"table:{table['id']}")]
        for table in tables
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def dates_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сегодня", callback_data="date:today")],
            [InlineKeyboardButton(text="Завтра", callback_data="date:tomorrow")],
        ]
    )


def slots_keyboard(slots: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []
    for slot in slots:
        if not slot["available"]:
            continue
        text = f"{slot['start_at'][11:16]} - {slot['end_at'][11:16]}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"slot:{slot['start_at']}|{slot['end_at']}")])
    if not keyboard:
        keyboard = [[InlineKeyboardButton(text="Нет доступных слотов", callback_data="noop")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def group_poster_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    link = f"https://t.me/{bot_username}?start=from_group"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Забронировать", url=link)]]
    )
