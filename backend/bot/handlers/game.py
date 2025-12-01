import uuid
import logging
from aiogram import Router, F, Bot
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton, ChosenInlineResult, CallbackQuery, InputMediaPhoto
)
from aiogram.exceptions import TelegramBadRequest
import html
from db.models.match import Match
from db.models.user import User
from bot.utils.game_utils import create_casual_questions

router = Router(name="game")

@router.inline_query()
async def handle_duel_start(query: InlineQuery):
    match_uid = str(uuid.uuid4())
    sender_id = query.from_user.id
    sender_name = html.escape(query.from_user.first_name)

    results = []

    join_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Join Match", callback_data=f"join_{match_uid}")]
    ])
    
    results.append(
        InlineQueryResultArticle(
            id=f"duel_{match_uid}",
            title="Create Flag Match",
            description="Challenge a friend to guess flags!",
            thumbnail_url="https://em-content.zobj.net/source/microsoft-teams/337/chequered-flag_1f3c1.png",
            input_message_content=InputTextMessageContent(
                message_text="<b>🚩 Flag Duel</b>\n\nWaiting for Players...",
                parse_mode="HTML"
            ),
            reply_markup=join_markup
        )
    )

    top_players = await User.all().order_by("-total_score").limit(10)
    
    lb_lines = ["<b>🏆 Flag Duel Hall of Fame</b>\n"]
    if not top_players:
        lb_lines.append("No players yet!")
    else:
        for i, p in enumerate(top_players, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lb_lines.append(f"{medal} <b>{html.escape(p.name)}</b> — {p.total_score} pts")
    
    lb_text = "\n".join(lb_lines)

    results.append(
        InlineQueryResultArticle(
            id=f"lb_{match_uid}",
            title="Share Leaderboard",
            description="Show the top 10 players!",
            thumbnail_url="https://em-content.zobj.net/source/microsoft-teams/337/trophy_1f3c6.png",
            input_message_content=InputTextMessageContent(
                message_text=lb_text,
                parse_mode="HTML"
            )
        )
    )
    
    await query.answer(results=results, cache_time=5, is_personal=True)

@router.chosen_inline_result()
async def handle_duel_accept(chosen: ChosenInlineResult):
    if not chosen.result_id.startswith("duel_"):
        return

    match_id = chosen.result_id.split("_")[1]

    user, _ = await User.get_or_create(
        id=chosen.from_user.id, 
        defaults={"name": chosen.from_user.first_name}
    )
    
    await Match.create(
        id=match_id,  
        host_id=user.id,
        participants=[user.id],
        inline_message_id=chosen.inline_message_id,
        scores={str(user.id): 0}
    )

@router.callback_query(F.data.startswith("join_"))
async def handle_join(callback: CallbackQuery):
    match_id = callback.data.split("_")[1]
    match = await Match.get_or_none(id=match_id)
    
    if not match or match.is_started:
        return await callback.answer("Match already started or invalid.", show_alert=True)
    
    user_id = callback.from_user.id
    
    if user_id not in match.participants:
        await User.get_or_create(id=user_id, defaults={"name": callback.from_user.first_name})
        
        match.participants.append(user_id)
        scores = match.scores
        scores[str(user_id)] = 0
        match.scores = scores
        await match.save()
    else:
        return await callback.answer("You are already in!", show_alert=True)

    count = len(match.participants)
    text = f"<b>🚩 Flag Duel Lobby</b>\n\nPlayers joined: {count}\nWaiting for host to start..."
    
    kb = [
        [InlineKeyboardButton(text="⚔️ Join Match", callback_data=f"join_{match.id}")],
        [InlineKeyboardButton(text="🚀 Start Game (Host)", callback_data=f"start_{match.id}")]
    ]
    
    await callback.bot.edit_message_text(
        inline_message_id=match.inline_message_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("start_"))
async def handle_start(callback: CallbackQuery):
    match_id = callback.data.split("_")[1]
    match = await Match.get(id=match_id)
    
    if callback.from_user.id != match.host_id:
        return await callback.answer("Only the host can start the game!", show_alert=True)
    
    if len(match.participants) < 2:
        return await callback.answer("Need at least 2 players!", show_alert=True)
    host = await User.get(id=match.host_id)
    
    if host.energy < 1:
        return await callback.answer(
            "⚡ Not enough energy to start!\nCheck the bot @flagduel_bot to buy more.", 
            show_alert=True
        )
    
    host.energy -= 1
    await host.save()
    match.is_started = True
    match.questions = await create_casual_questions(5) 
    await match.save()
    
    await render_question(match, callback.bot)

async def render_question(match: Match, bot: Bot):
    q_idx = match.current_question_idx
    if q_idx >= len(match.questions):
        return await render_game_over(match, bot)

    question = match.questions[q_idx]
    
    keyboard = []
    row = []
    for opt in question["options"]:
        opt_idx = question["options"].index(opt)
        row.append(InlineKeyboardButton(text=opt, callback_data=f"ans_{match.id}_{opt_idx}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = (
        f"<b>Question {q_idx + 1}/{len(match.questions)}</b>\n"
        f"<i>Which flag is this?</i>"
    )
    
        
    try:
        await bot.edit_message_media(
            inline_message_id=match.inline_message_id,
            media=InputMediaPhoto(media=question["image"], caption=text, parse_mode="HTML"),
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        logging.error(f"Failed to update inline message: {e}")

@router.callback_query(F.data.startswith("ans_"))
async def handle_answer(callback: CallbackQuery):
    _, match_id, ans_idx = callback.data.split("_")
    ans_idx = int(ans_idx)
    user_id = callback.from_user.id 
    
    match = await Match.get_or_none(id=match_id)

    if not match: 
        return await callback.answer("Error: Match not found", show_alert=True)

    if user_id not in match.participants:
        return await callback.answer("You are not in this match!", show_alert=True)
    
    current_round_answers = match.current_round_answers or {}
    if str(user_id) in current_round_answers:
         return await callback.answer("You already answered! Waiting for others...", show_alert=True)

    q_data = match.questions[match.current_question_idx]
    selected_option = q_data["options"][ans_idx]
    
    current_round_answers[str(user_id)] = selected_option
    match.current_round_answers = current_round_answers
    await match.save()

    await callback.answer("Answer received! ⏳")

    if len(current_round_answers) >= len(match.participants):
        await process_round_results(match, callback.bot)
    else:
        remaining = len(match.participants) - len(current_round_answers)

async def process_round_results(match: Match, bot: Bot):
    q_data = match.questions[match.current_question_idx]
    correct_ans = q_data["correct_answer"]  

    players = await User.filter(id__in=match.participants).all()
    player_map = {str(u.id): u for u in players}

    scores = match.scores 
    
    results_text_lines = []
    
    for user_id_str in match.current_round_answers:
        user_ans = match.current_round_answers[user_id_str]
        is_correct = (user_ans == correct_ans)
        
        if is_correct:
            scores[user_id_str] = scores.get(user_id_str, 0) + 1
            
        p_name = player_map[user_id_str].name if user_id_str in player_map else "Unknown"
        icon = "✅" if is_correct else "❌"
        
        safe_name = html.escape(p_name)
        safe_ans = html.escape(user_ans)
        
        results_text_lines.append(f"{safe_name}: {icon} ({safe_ans})")

    match.scores = scores
    match.current_round_answers = {}
    await match.save()
    

    safe_correct = html.escape(correct_ans)
    joined_results = "\n".join(results_text_lines)
    
    text = (
        f"<b>Results:</b>\n"
        f"🏁 Correct: <b>{safe_correct}</b>\n\n"
        f"{joined_results}"
    )
    

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Next Question ⏭️", 
            callback_data=f"next_{match.id}"
        )]
    ])
    
    await bot.edit_message_caption(
        inline_message_id=match.inline_message_id,
        caption=text,
        reply_markup=markup,
        parse_mode="HTML"
    )
    

@router.callback_query(F.data.startswith("next_"))
async def handle_next(callback: CallbackQuery):
    match_id = callback.data.split("_")[1]
    match = await Match.get(id=match_id)
    user_id = callback.from_user.id
    
    if user_id not in match.participants:
        return await callback.answer("You are not in this game.")

    if user_id not in match.ready_players:
        match.ready_players.append(user_id)
        await match.save()

    total_players = len(match.participants)
    ready_count = len(match.ready_players)

    if ready_count >= total_players:
        match.current_question_idx += 1
        match.ready_players = [] 
        await match.save()
        await render_question(match, callback.bot)
    else:
        await callback.answer("Waiting for others...")
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"Next Question ⏭️ ({ready_count}/{total_players})", 
                callback_data=f"next_{match.id}"
            )]
        ])
        
        try:
            await callback.bot.edit_message_reply_markup(
                inline_message_id=match.inline_message_id,
                reply_markup=markup
            )
        except Exception:
            pass 

async def render_game_over(match: Match, bot: Bot):
    participants = await User.filter(id__in=match.participants).all()
    
    user_map = {str(u.id): u.name for u in participants}
    

    leaderboard = []
    for user_id, score in match.scores.items():
        name = user_map.get(user_id, "Unknown Player")
        leaderboard.append((name, score))
    
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    
    if not leaderboard:
        winner_text = "No one played!"
    elif len(leaderboard) > 1 and leaderboard[0][1] == leaderboard[1][1]:
        winner_text = "It's a Draw! 🤝"
    else:
        winner_name = html.escape(leaderboard[0][0])
        winner_text = f"🏆 {winner_name} Wins!"

    score_lines = []
    for i, (name, score) in enumerate(leaderboard, 1):
        medal = ""
        if i == 1: medal = "🥇 "
        elif i == 2: medal = "🥈 "
        elif i == 3: medal = "🥉 "
        
        safe_name = html.escape(name)
        score_lines.append(f"{medal}{i}. <b>{safe_name}</b>: {score}")

    score_text = "\n".join(score_lines)

    text = (
        f"<b>🏁 GAME OVER 🏁</b>\n\n"
        f"{winner_text}\n"
        f"----------------\n"
        f"{score_text}"
    )

    await bot.edit_message_caption(
        inline_message_id=match.inline_message_id,
        caption=text,
        reply_markup=None,
        parse_mode="HTML"
    )
