from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery
from db.models.user import User
from config_reader import bot
from tortoise.exceptions import DoesNotExist
router = Router(name="payment")

@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    print("ok")
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    
    await bot.refund_star_payment(
        message.from_user.id, 
        message.successful_payment.telegram_payment_charge_id
    )

    if payload.startswith("energy_"):
        try:
            energy_amount = int(payload.split("_")[1])
            
            user = await User.get(id=user_id)
            user.energy += energy_amount
            await user.save()
            
            await message.answer(
                f"✅ <b>Payment Successful!</b>\n"
                f"Added {energy_amount} ⚡ energy.\n"
                f"Current Energy: {user.energy}",
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer("⚠️ Error processing energy payment. Contact support.")
            print(f"Payment Error: {e}")
    elif payload.startswith("energy_gift_"):
        parts = payload.split("_")
        target_id = int(parts[2])
        amount = int(parts[3])
        
        try:
            target_user = await User.get(id=target_id)
            target_user.energy += amount
            await target_user.save()
            

            import html
            receiver_name = html.escape(target_user.name)
            
            await message.answer(
                f"✅ <b>Gift Sent!</b>\n"
                f"You successfully donated {amount} ⚡ energy to <b>{receiver_name}</b>.",
                parse_mode="HTML"
            )

        except DoesNotExist:
            await message.answer("⚠️ The user you tried to gift no longer exists in our database.")
        except Exception as e:
            print(f"Gift Error: {e}")
            await message.answer("⚠️ An error occurred while processing the gift.")
