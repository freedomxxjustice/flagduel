import html
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.filters import CommandStart

from db.models.user import User
from bot.keyboards import main_markup, get_energy_markup 

router = Router(name="common")

@router.message(CommandStart())
async def start(message: Message) -> None:
    await User.get_or_create(
        id=message.from_user.id, 
        defaults={"name": message.from_user.first_name, "energy": 5}
    )
    
    await message.answer(
        "Welcome to Flag Duel! 🚩\nChoose an option below:",
        reply_markup=main_markup,
    )

@router.message(F.text == "🏆 Leaderboard")
async def show_leaderboard(message: Message):
    user_id = message.from_user.id
    
    top_players = await User.all().order_by("-total_score").limit(10)

    user = await User.get_or_none(id=user_id)
    if not user:
        return await message.answer("Please type /start first.")
        
    rank = await User.filter(total_score__gt=user.total_score).count() + 1
    
    lines = ["<b>🏆 Hall of Fame 🏆</b>\n"]
    for i, p in enumerate(top_players, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        name = html.escape(p.name)
        lines.append(f"{medal} <b>{name}</b> — {p.total_score} pts")
    
    lines.append(f"\n👤 <b>Your Rank:</b> #{rank}")
    lines.append(f"⚡ <b>Your Energy:</b> {user.energy}")

    await message.answer("\n".join(lines), parse_mode="HTML")

@router.message(F.text == "⚡ Buy Energy")
async def buy_energy_menu(message: Message):
    user = await User.get(id=message.from_user.id)
    await message.answer(
        f"⚡ <b>Energy Shop</b>\n"
        f"You have {user.energy} energy.\n"
        f"Energy is required to start new matches.\n\n"
        f"Select a pack to buy with Telegram Stars:",
        reply_markup=get_energy_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("buy_energy_"))
async def send_energy_invoice(callback: CallbackQuery):
    amount_str = callback.data.split("_")[2]
    amount = int(amount_str)
    
    price_map = {5: 10, 15: 25, 50: 50}
    stars_price = price_map.get(amount)
    
    await callback.message.answer_invoice(
        title=f"{amount} Energy Pack",
        description=f"Refill {amount} energy for Flag Duel.",
        payload=f"energy_{amount}", 
        currency="XTR", 
        prices=[LabeledPrice(label="Energy", amount=stars_price)], 
        provider_token="" 
    )
    await callback.answer()