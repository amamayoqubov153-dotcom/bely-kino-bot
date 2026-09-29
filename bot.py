```python
import asyncio
import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# =========================
# SOZLAMALAR
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ADMIN ID
ADMIN_ID = 8251493317

# MAJBURIY TELEGRAM KANALLAR
CHANNELS = [
    "@bely_kino",
    "@bely_kino_chat",
]

# INSTAGRAM
INSTAGRAM_URL = "https://www.instagram.com/bely.kino"

# DATABASE
DB_NAME = "kino.db"


# =========================
# TOKEN TEKSHIRISH
# =========================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi. Render Environment Variables "
        "ichida BOT_TOKEN qo'shing."
    )


# =========================
# BOT
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def add_movie(code, file_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO movies (code, file_id)
        VALUES (?, ?)
        """,
        (code, file_id)
    )

    conn.commit()
    conn.close()


def get_movie(code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT file_id FROM movies WHERE code = ?",
        (code,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return None


def delete_movie(code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM movies WHERE code = ?",
        (code,)
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted > 0


# =========================
# MAJBURIY OBUNA
# =========================

async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )

            if member.status in ["left", "kicked"]:
                return False

        except Exception as error:
            logging.error(
                f"{channel} tekshirishda xato: {error}"
            )
            return False

    return True


def subscription_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                text="📢 @bely_kino",
                url="https://t.me/bely_kino"
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 @bely_kino_chat",
                url="https://t.me/bely_kino_chat"
            )
        ],
        [
            InlineKeyboardButton(
                text="📸 Instagram",
                url=INSTAGRAM_URL
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Obunani tekshirish",
                callback_data="check_subscription"
            )
        ]
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


async def require_subscription(message: Message):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if subscribed:
        return True

    await message.answer(
        "🎬 <b>BELY KINO</b>\n\n"
        "Botdan foydalanish uchun avval "
        "quyidagi Telegram kanallariga obuna bo'ling 👇\n\n"
        "📢 @bely_kino\n"
        "💬 @bely_kino_chat\n\n"
        "Obuna bo'lgach, "
        "<b>✅ Obunani tekshirish</b> tugmasini bosing.",
        reply_markup=subscription_keyboard()
    )

    return False


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start_handler(message: Message):

    if not await require_subscription(message):
        return

    await message.answer(
        "🎬 <b>BELY KINO</b>\n\n"
        "🍿 Kino olish uchun kino kodini yuboring.\n\n"
        "Masalan:\n"
        "<code>1234</code>\n\n"
        "🔎 Kino kodini yuboring."
    )


# =========================
# OBUNANI TEKSHIRISH
# =========================

@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(
    callback: CallbackQuery
):

    subscribed = await check_subscription(
        callback.from_user.id
    )

    if subscribed:

        await callback.message.edit_text(
            "✅ <b>Obuna tasdiqlandi!</b>\n\n"
            "🎬 Endi kino kodini yuboring."
        )

        await callback.answer()

    else:

        await callback.answer(
            "❌ Hali barcha kanallarga obuna bo'lmagansiz.",
            show_alert=True
        )


# =========================
# KINO QO'SHISH HOLATLARI
# =========================

class AddMovieState(StatesGroup):
    waiting_code = State()
    waiting_video = State()


# =========================
# ADMIN /ADD
# =========================

@dp.message(Command("add"))
async def add_movie_start(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    await state.set_state(
        AddMovieState.waiting_code
    )

    await message.answer(
        "🎬 <b>Kino qo'shish</b>\n\n"
        "1️⃣ Kino kodini yuboring.\n\n"
        "Masalan: <code>1234</code>"
    )


# =========================
# KINO KODINI QABUL QILISH
# =========================

@dp.message(AddMovieState.waiting_code)
async def add_movie_code(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    code = message.text.strip()

    await state.update_data(
        code=code
    )

    await state.set_state(
        AddMovieState.waiting_video
    )

    await message.answer(
        f"✅ Kino kodi: <code>{code}</code>\n\n"
        "2️⃣ Endi kino videosini yuboring."
    )


# =========================
# VIDEONI SAQLASH
# =========================

@dp.message(
    AddMovieState.waiting_video,
    F.video
)
async def add_movie_video(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()

    code = data["code"]

    file_id = message.video.file_id

    add_movie(
        code,
        file_id
    )

    await state.clear()

    await message.answer(
        "✅ <b>Kino muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🎬 Kod: <code>{code}</code>\n"
        "📁 Video saqlandi."
    )


# =========================
# ADMIN /DELETE
# =========================

@dp.message(Command("delete"))
async def delete_command(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🗑 Kino o'chirish:\n\n"
        "<code>/delete 1234</code>"
    )


@dp.message(F.text.startswith("/delete "))
async def delete_movie_handler(
    message: Message
):

    if message.from_user.id != ADMIN_ID:
        return

    code = message.text.split(
        maxsplit=1
    )[1].strip()

    if delete_movie(code):

        await message.answer(
            "✅ Kino o'chirildi.\n\n"
            f"🔑 Kod: <code>{code}</code>"
        )

    else:

        await message.answer(
            "❌ Bu kod bo'yicha kino topilmadi."
        )


# =========================
# KINO KODINI QIDIRISH
# =========================

@dp.message(F.text)
async def movie_code_handler(
    message: Message
):

    # Buyruqlarni o'tkazib yuborish
    if message.text.startswith("/"):
        return

    if not await require_subscription(message):
        return

    code = message.text.strip()

    file_id = get_movie(code)

    if not file_id:

        await message.answer(
            "❌ <b>Kino topilmadi.</b>\n\n"
            "🔎 Kino kodini tekshirib qayta yuboring."
        )

        return

    await message.answer_video(
        video=file_id,
        caption=(
            "🎬 <b>BELY KINO</b>\n\n"
            f"🔑 Kino kodi: <code>{code}</code>\n\n"
            "🍿 Yoqimli tomosha!"
        )
    )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

async def main():

    logging.basicConfig(
        level=logging.INFO
    )

    init_db()

    print(
        "🎬 BELY KINO bot ishga tushdi!"
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```
