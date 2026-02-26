import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ─── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = "7842828259:AAHbMZRllAQUROyVW2VRIVczswOPI0cbR78"          # Вставь токен от @BotFather
ADMIN_IDS = [893992849]                  # Вставь свой Telegram ID (узнать: @userinfobot)
USERS_FILE = "users.json"               # База подписчиков

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ─── База пользователей ───────────────────────────────────────────────────────
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def add_user(user):
    users = load_users()
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "id": user.id,
            "first_name": user.first_name or "",
            "username": user.username or "",
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_users(users)
        return True
    return False


# ─── FAQ ──────────────────────────────────────────────────────────────────────
FAQ = {
    "📅 Когда вебинар?": "Презентация курса пройдёт **1 марта в 19:00**. Обязательно приходи — будет много пользы, практика и подарки 🎁",
    "🎓 Для кого курс?": "Курс подойдёт всем, кто хочет развить голос: начинающим и тем, кто уже поёт. Мы работаем с техникой, дыханием и уверенностью на сцене 🎤",
    "💰 Сколько стоит?": "Цены будут объявлены на презентации 1 марта. Участники вебинара получат самые выгодные условия — только в этот вечер 🔥",
    "🎁 Что будет на вебинаре?": "На вебинаре: разберём важные вокальные темы, попрактикуемся вместе, а все, кто останется до конца — получат подарки от меня лично 🎶",
    "🔗 Ссылка на вебинар": "Ссылку пришлём перед эфиром — убедись, что подписан(а) на бота, чтобы не пропустить 📩",
}


# ─── Главное меню ─────────────────────────────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📅 Когда вебинар?", "🎓 Для кого курс?"],
            ["💰 Сколько стоит?", "🎁 Что будет на вебинаре?"],
            ["🔗 Ссылка на вебинар"],
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📣 Рассылка", "👥 Кол-во подписчиков"],
            ["⏰ Напомнить о вебинаре", "🏠 Главное меню"],
        ],
        resize_keyboard=True
    )


# ─── Хэндлеры ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = add_user(user)

    greeting = f"Привет, {user.first_name}! 👋\n\n" if is_new else f"С возвращением, {user.first_name}! 👋\n\n"

    text = (
        greeting
        + "Я помогу тебе узнать всё о нашем курсе и напомню о предстоящем вебинаре 🎤\n\n"
        + "📅 *1 марта в 19:00* — презентация курса. Там тебя ждут:\n"
        + "• Важные вокальные темы\n"
        + "• Живая практика\n"
        + "• Подарки всем, кто будет от начала до конца 🎁\n"
        + "• Самые выгодные цены на курс\n\n"
        + "Выбери вопрос ниже 👇"
    )

    await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")


async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text in FAQ:
        await update.message.reply_text(FAQ[text], parse_mode="Markdown")
        return

    # Админские команды
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Я не понял вопрос 🤔 Используй кнопки ниже.", reply_markup=main_keyboard())
        return

    if text == "🏠 Главное меню":
        await update.message.reply_text("Главное меню:", reply_markup=main_keyboard())

    elif text == "👥 Кол-во подписчиков":
        count = len(load_users())
        await update.message.reply_text(f"👥 Подписчиков в базе: *{count}*", parse_mode="Markdown")

    elif text == "⏰ Напомнить о вебинаре":
        await send_webinar_reminder(update, context)

    elif text == "📣 Рассылка":
        context.user_data["waiting_broadcast"] = True
        await update.message.reply_text(
            "✏️ Напиши текст рассылки, и я отправлю его всем подписчикам.\n\n"
            "Для отмены напиши /cancel"
        )


async def handle_broadcast_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_broadcast"):
        return
    if update.effective_user.id not in ADMIN_IDS:
        return

    context.user_data["waiting_broadcast"] = False
    broadcast_text = update.message.text
    users = load_users()
    success, fail = 0, 0

    await update.message.reply_text(f"⏳ Начинаю рассылку {len(users)} пользователям...")

    for uid, info in users.items():
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=broadcast_text,
                parse_mode="Markdown"
            )
            success += 1
        except Exception:
            fail += 1

    await update.message.reply_text(
        f"✅ Рассылка завершена!\n\n"
        f"📨 Отправлено: {success}\n"
        f"❌ Ошибок: {fail}",
        reply_markup=admin_keyboard()
    )


async def send_webinar_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminder_text = (
        "🔔 *Напоминание!*\n\n"
        "Уже завтра — *1 марта в 19:00* — презентация курса 🎤\n\n"
        "Тебя ждут:\n"
        "🎵 Живая вокальная практика\n"
        "🧠 Важные темы, которые изменят твой голос\n"
        "🎁 Подарки всем, кто останется до конца\n"
        "💥 Самые выгодные цены на курс — только в эту ночь!\n\n"
        "Не пропусти! Ссылка придёт за час до начала 👇"
    )

    users = load_users()
    success, fail = 0, 0

    await update.message.reply_text(f"⏳ Отправляю напоминание {len(users)} пользователям...")

    for uid in users:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=reminder_text,
                parse_mode="Markdown"
            )
            success += 1
        except Exception:
            fail += 1

    await update.message.reply_text(
        f"✅ Напоминание отправлено!\n\n"
        f"📨 Успешно: {success}\n"
        f"❌ Ошибок: {fail}",
        reply_markup=admin_keyboard()
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Нет доступа.")
        return
    await update.message.reply_text("👑 Панель администратора:", reply_markup=admin_keyboard())


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Отменено.", reply_markup=main_keyboard())


# ─── Запуск ───────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("cancel", cancel))

    # Сначала проверяем ввод рассылки, потом FAQ
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_input), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_faq), group=1)

    print("🤖 Бот запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
