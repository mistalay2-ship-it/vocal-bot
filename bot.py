import logging
import json
import os
from datetime import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# ─── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "7842828259:AAHbMZRllAQUROyVW2VRIVczswOPI0cbR78")
ADMIN_IDS = [int(os.getenv("ADMIN_ID", "893992849"))]
USERS_FILE = "users.json"

# 🕐 Твой часовой пояс
# Варианты: "Europe/Moscow", "Europe/Kiev", "Asia/Almaty", "Europe/Minsk"
TIMEZONE = pytz.timezone("Europe/Moscow")

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


# ─── FAQ (редактируй текст ответов здесь!) ────────────────────────────────────
FAQ = {
    "📅 Когда вебинар?": (
        "Презентация курса пройдёт *1 марта в 19:00* 🎤\n\n"
        "Обязательно приходи — будет много пользы, живая практика и подарки 🎁"
    ),
    "🎓 Для кого курс?": (
        "Курс подойдёт всем, кто хочет развить голос: начинающим и тем, кто уже поёт 🎶\n\n"
        "Мы работаем с техникой, мышцами и уверенностью в своих силах 🎤"
    ),
    "💰 Сколько стоит?": (
        "Цены будут объявлены на презентации *1 марта* в конце вебинара 🔥\n\n"
        "Участники вебинара получат самые выгодные условия — только в этот вечер!\n"
        "После презентации цена вырастет, так что не пропусти 😉"
    ),
    "🎁 Что будет на вебинаре?": (
        "На вебинаре тебя ждёт:\n\n"
        "🎵 Живая вокальная практика прямо на эфире\n"
        "🧠 Важные темы, очень знакомые, но такие важные: голосовые складки, гортань, небо, современные реалии педагога вокала и, конечно, ИИ\n"
        "🎁 Подарки всем, кто останется от начала до конца: авторское упражнение 3 в 1 с минусовкой и нотами, а также гайд по самостоятельной работе с ИИ инструментами\n"
        "💥 Самые выгодные цены на курс — только в эту ночь!"
    ),
    "🔗 Ссылка на вебинар": (
        "Ссылку пришлём прямо в этот бот за час до начала 📩\n\n"
        "Убедись, что не заблокировал(а) бота — иначе сообщение не дойдёт!\n"
        "До встречи 1 марта в 19:00 🎤"
    ),
}


# ─── Клавиатуры ───────────────────────────────────────────────────────────────
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


# ─── Авторассылка по расписанию ───────────────────────────────────────────────
async def auto_reminder_day_before(context):
    """28 февраля в 12:00 — напоминание за день"""
    text = (
        "🔔 *Напоминаем — завтра вебинар!*\n\n"
        "📅 *1 марта в 19:00* — встречаемся на презентации курса!\n\n"
        "Тебя ждут:\n"
        "🎵 Живая вокальная практика\n"
        "🧠 Важные темы, очень знакомые, но такие важные: голосовые складки, гортань, небо, современные реалии педагога вокала и, конечно, ИИ\n"
        "🎁 Подарки всем, кто останется от начала до конца: авторское упражнение 3 в 1 с минусовкой и нотами, а также гайд по самостоятельной работе с ИИ инструментами\n"
        "💥 Специальные цены — только на этом эфире\n\n"
        "Ссылка придёт за час до начала прямо сюда 👇"
    )
    await broadcast_to_all(context.bot, text)

async def auto_reminder_hour_before(context):
    """1 марта в 18:00 — напоминание за час"""
    text = (
        "⏰ *Через час начинаем!*\n\n"
        "Уже сегодня в *19:00* — презентация курса 🎤\n\n"
        "Подготовься:\n"
        "✅ Найди удобное место\n"
        "✅ Возьми обязательно воды 💧\n"
        "✅ Приготовься петь и практиковаться!\n\n"
        "Ссылка на эфир 👇\n"
        "_(https://start.bizon365.ru/room/149439/a0a2ad06b401)_"
    )
    await broadcast_to_all(context.bot, text)

async def auto_reminder_starting_now(context):
    """1 марта в 19:00 — начинаем!"""
    text = (
        "🔴 *Мы начинаем прямо сейчас!*\n\n"
        "Заходи скорее — вебинар уже идёт! 🎤\n\n"
        "👇 Ссылка для входа:\n"
        "_(https://start.bizon365.ru/room/149439/a0a2ad06b401)_\n\n"
        "Жду тебя! 🎁"
    )
    await broadcast_to_all(context.bot, text)

async def broadcast_to_all(bot, text):
    users = load_users()
    success, fail = 0, 0
    for uid in users:
        try:
            await bot.send_message(chat_id=int(uid), text=text, parse_mode="Markdown")
            success += 1
        except Exception:
            fail += 1
    logging.info(f"Авторассылка: отправлено {success}, ошибок {fail}")


# ─── Хэндлеры ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = add_user(user)
    greeting = f"Привет, {user.first_name}! 👋\n\n" if is_new else f"С возвращением, {user.first_name}! 👋\n\n"
    text = (
        greeting
        + "Я помогу тебе узнать всё о курсе и пришлю напоминание о вебинаре 🎤\n\n"
        + "📅 *1 марта в 19:00* — презентация курса:\n"
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
            "✏️ Напиши текст рассылки — я отправлю его всем подписчикам.\n\nДля отмены напиши /cancel"
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
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=broadcast_text, parse_mode="Markdown")
            success += 1
        except Exception:
            fail += 1

    await update.message.reply_text(
        f"✅ Рассылка завершена!\n\n📨 Отправлено: {success}\n❌ Ошибок: {fail}",
        reply_markup=admin_keyboard()
    )


async def send_webinar_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminder_text = (
        "🔔 *Напоминание о вебинаре!*\n\n"
        "Уже скоро — *1 марта в 19:00* — презентация курса 🎤\n\n"
        "🎵 Живая вокальная практика\n"
        "🧠 Важные темы, очень знакомые, но такие важные: голосовые складки, гортань, небо, современные реалии педагога вокала и, конечно, ИИ\n"
        "🎁 Подарки всем, кто останется от начала до конца: авторское упражнение 3 в 1 с минусовкой и нотами, а также гайд по самостоятельной работе с ИИ инструментами\n"
        "💥 Специальные цены — только на этом эфире\n\n"
        "Ссылка придёт за час до начала прямо сюда 👇"
    )
    users = load_users()
    success, fail = 0, 0

    await update.message.reply_text(f"⏳ Отправляю напоминание {len(users)} пользователям...")
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=reminder_text, parse_mode="Markdown")
            success += 1
        except Exception:
            fail += 1

    await update.message.reply_text(
        f"✅ Напоминание отправлено!\n\n📨 Успешно: {success}\n❌ Ошибок: {fail}",
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_input), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_faq), group=1)

    # ⏰ Автоматические напоминания
    job_queue = app.job_queue

    # 28 февраля в 12:00 — напоминание за день (пятница = день 4)
    job_queue.run_daily(
        auto_reminder_day_before,
        time=datetime.strptime("12:00", "%H:%M").replace(tzinfo=TIMEZONE).timetz(),
        days=(4,),
        name="reminder_day_before"
    )

    # 1 марта в 18:00 — за час (суббота = день 5)
    job_queue.run_daily(
        auto_reminder_hour_before,
        time=datetime.strptime("18:00", "%H:%M").replace(tzinfo=TIMEZONE).timetz(),
        days=(5,),
        name="reminder_hour_before"
    )

    # 1 марта в 19:00 — начинаем! (суббота = день 5)
    job_queue.run_daily(
        auto_reminder_starting_now,
        time=datetime.strptime("19:00", "%H:%M").replace(tzinfo=TIMEZONE).timetz(),
        days=(5,),
        name="reminder_start"
    )

    print("🤖 Бот запущен с автонапоминаниями!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
