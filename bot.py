import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


# =========================
# SOZLAMALAR
# =========================

BOT_TOKEN = 8978066534:AAGYLe-lKWM6qM9MPuFbYVy6TUu4bvbeCVk

ADMIN_ID = 8251493317

CHANNEL_1 = "@bely_kino"
CHANNEL_2 = "@bely_kino_chat"

INSTAGRAM_URL = "https://www.instagram.com/bely.kino?stkn=MTh1c20wMmlhN2k2"


# =========================
# BOT
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)


# =========================
# DATABASE
# =========================

db = sqlite3.connect("movies.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    file_id TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT
)
""")

db.commit()


# =========================
# FSM
# =========================

class AddMovie(StatesGroup):
    code = State()
    title = State()
    description = State()
    video = State()


# =========================
# KLAVIATURALAR
# =========================

def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 BELY KINO",
                    url="https://t.me/bely_kino"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 BELY KINO CHAT",
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
    )


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎬 Kino qidirish",
                    callback_data="search_movie"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📸 Instagram",
                    url=INSTAGRAM_URL
                )
            ]
        ]
    )


def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Kino qo‘shish",
                    callback_data="admin_add"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Kinolar ro‘yxati",
                    callback_data="admin_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Kino o‘chirish",
                    callback_data="admin_delete"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Statistika",
                    callback_data="admin_stats"
                )
            ]
        ]
    )


# =========================
# OBUNANI TEKSHIRISH
# =========================

async def check_subscription(user_id: int) -> bool:

    for channel in [CHANNEL_1, CHANNEL_2]:

        try:
            member = await bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )

            if member.status in ["left", "kicked"]:
                return False

        except Exception as e:
            logging.error(
                f"{channel} tekshirishda xato: {e}"
            )
            return False

    return True


# =========================
# USER SAQLASH
# =========================

def save_user(message: Message):

    user = message.from_user

    cursor.execute("""
    INSERT OR REPLACE INTO users
    (user_id, username, first_name)
    VALUES (?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    db.commit()


# =========================
# /START
# =========================

@dp.message(Command("start"))
async def start_handler(message: Message):

    save_user(message)

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "🎬 <b>BELY KINO</b>\n\n"
            "Botdan foydalanish uchun quyidagi kanallarga "
            "obuna bo‘ling 👇\n\n"
            "1️⃣ @bely_kino\n"
            "2️⃣ @bely_kino_chat\n\n"
            "Obuna bo‘lganingizdan keyin "
            "<b>✅ Obunani tekshirish</b> tugmasini bosing.",
            reply_markup=subscription_keyboard(),
            parse_mode="HTML"
        )

        return

    await message.answer(
        "🎬 <b>BELY KINO</b>\n\n"
        "🍿 Kino olamiga xush kelibsiz!\n\n"
        "🎥 Kino kodini yuboring va filmingizni oling.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


# =========================
# OBUNANI QAYTA TEKSHIRISH
# =========================

@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(
    callback: CallbackQuery
):

    subscribed = await check_subscription(
        callback.from_user.id
    )

    if not subscribed:

        await callback.answer(
            "❌ Hali barcha kanallarga obuna bo‘lmagansiz!",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "🎬 <b>BELY KINO</b>\n\n"
        "✅ Obunangiz tasdiqlandi!\n\n"
        "🎥 Kino kodini yuboring.",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# KINO QIDIRISH TUGMASI
# =========================

@dp.callback_query(F.data == "search_movie")
async def search_movie_callback(
    callback: CallbackQuery
):

    await callback.message.answer(
        "🎬 Kino kodini yuboring.\n\n"
        "Masalan:\n"
        "<code>1001</code>",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ADMIN PANEL
# =========================

@dp.message(Command("admin"))
async def admin_command(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "👨‍💻 <b>ADMIN PANEL</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )


# =========================
# ADMIN KINO QO‘SHISH
# =========================

@dp.callback_query(F.data == "admin_add")
async def admin_add_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id != ADMIN_ID:
        return

    await state.set_state(AddMovie.code)

    await callback.message.answer(
        "➕ <b>Kino qo‘shish</b>\n\n"
        "Kino kodini yuboring.\n\n"
        "Masalan: <code>1001</code>",
        parse_mode="HTML"
    )

    await callback.answer()


@dp.message(AddMovie.code)
async def add_movie_code(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    code = message.text.strip()

    cursor.execute(
        "SELECT id FROM movies WHERE code = ?",
        (code,)
    )

    if cursor.fetchone():

        await message.answer(
            "❌ Bu kod allaqachon mavjud.\n"
            "Boshqa kod yuboring."
        )

        return

    await state.update_data(code=code)

    await state.set_state(AddMovie.title)

    await message.answer(
        "🎬 Kino nomini yuboring:"
    )


@dp.message(AddMovie.title)
async def add_movie_title(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(
        title=message.text.strip()
    )

    await state.set_state(AddMovie.description)

    await message.answer(
        "📝 Kino haqida qisqa ma'lumot yuboring.\n\n"
        "Agar kerak bo‘lmasa <code>-</code> yuboring.",
        parse_mode="HTML"
    )


@dp.message(AddMovie.description)
async def add_movie_description(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    description = message.text.strip()

    if description == "-":
        description = ""

    await state.update_data(
        description=description
    )

    await state.set_state(AddMovie.video)

    await message.answer(
        "🎥 Endi kinoning videosini shu yerga yuboring."
    )


@dp.message(AddMovie.video, F.video)
async def add_movie_video(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()

    code = data["code"]
    title = data["title"]
    description = data["description"]

    file_id = message.video.file_id

    cursor.execute("""
    INSERT INTO movies
    (code, title, description, file_id)
    VALUES (?, ?, ?, ?)
    """, (
        code,
        title,
        description,
        file_id
    ))

    db.commit()

    await state.clear()

    await message.answer(
        "✅ <b>Kino muvaffaqiyatli qo‘shildi!</b>\n\n"
        f"🎬 Nomi: <b>{title}</b>\n"
        f"🔢 Kodi: <code>{code}</code>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


@dp.message(AddMovie.video)
async def wrong_movie_video(
    message: Message
):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "❌ Iltimos, kinoni <b>video</b> sifatida yuboring.",
        parse_mode="HTML"
    )


# =========================
# KINOLAR RO‘YXATI
# =========================

@dp.callback_query(F.data == "admin_list")
async def admin_list(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT code, title
    FROM movies
    ORDER BY id DESC
    """)

    movies = cursor.fetchall()

    if not movies:

        await callback.message.answer(
            "📭 Hozircha kinolar mavjud emas."
        )

        await callback.answer()

        return

    text = "📋 <b>KINOLAR RO‘YXATI</b>\n\n"

    for code, title in movies:

        text += (
            f"🎬 <b>{title}</b>\n"
            f"🔢 Kod: <code>{code}</code>\n\n"
        )

    await callback.message.answer(
        text,
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# KINO O‘CHIRISH
# =========================

@dp.callback_query(F.data == "admin_delete")
async def admin_delete_start(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return

    await callback.message.answer(
        "🗑 O‘chirmoqchi bo‘lgan kino kodini yuboring.\n\n"
        "Masalan: <code>1001</code>",
        parse_mode="HTML"
    )

    await callback.answer()


@dp.message(Command("delete"))
async def delete_movie(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            "❌ To‘g‘ri format:\n"
            "<code>/delete 1001</code>",
            parse_mode="HTML"
        )

        return

    code = parts[1]

    cursor.execute(
        "SELECT title FROM movies WHERE code = ?",
        (code,)
    )

    movie = cursor.fetchone()

    if not movie:

        await message.answer(
            "❌ Bunday kodli kino topilmadi."
        )

        return

    cursor.execute(
        "DELETE FROM movies WHERE code = ?",
        (code,)
    )

    db.commit()

    await message.answer(
        f"✅ <b>{movie[0]}</b> o‘chirildi.",
        parse_mode="HTML"
    )


# =========================
# STATISTIKA
# =========================

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    users_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM movies"
    )

    movies_count = cursor.fetchone()[0]

    await callback.message.answer(
        "📊 <b>STATISTIKA</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users_count}</b>\n"
        f"🎬 Kinolar: <b>{movies_count}</b>",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# KINO KODI QABUL QILISH
# =========================

@dp.message(F.text)
async def movie_code_handler(
    message: Message
):

    # Admin FSM ishlatayotgan bo‘lsa,
    # bu handler aralashmaydi.
    if message.from_user.id == ADMIN_ID:
        return

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun avval "
            "kanallarga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    code = message.text.strip()

    cursor.execute("""
    SELECT title, description, file_id
    FROM movies
    WHERE code = ?
    """, (code,))

    movie = cursor.fetchone()

    if not movie:

        await message.answer(
            "❌ <b>Kino topilmadi.</b>\n\n"
            "🔢 Kino kodini tekshirib qayta yuboring.",
            parse_mode="HTML"
        )

        return

    title, description, file_id = movie

    caption = f"🎬 <b>{title}</b>"

    if description:
        caption += f"\n\n📝 {description}"

    caption += "\n\n🍿 <b>BELY KINO</b>"

    await message.answer_video(
        video=file_id,
        caption=caption,
        parse_mode="HTML"
    )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

async def main():

    print("🎬 BELY KINO BOT ISHLAMOQDA...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
