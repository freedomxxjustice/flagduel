from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏆 Leaderboard"), KeyboardButton(text="⚡ Buy Energy")], 
    ],
    resize_keyboard=True,
    is_persistent=True
)

def get_energy_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 Energy (10 ⭐️)", callback_data="buy_energy_5")],
        [InlineKeyboardButton(text="15 Energy (25 ⭐️)", callback_data="buy_energy_15")],
        [InlineKeyboardButton(text="50 Energy (50 ⭐️)", callback_data="buy_energy_50")],
    ])