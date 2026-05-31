import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("family.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    partner_id INTEGER,
    parent_id INTEGER
)
""")
conn.commit()


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()


def create_user(user_id):
    if not get_user(user_id):
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()


@dp.message(Command("start"))
async def start(msg: Message):
    create_user(msg.from_user.id)
    await msg.answer("👋 Привет! Команды:\n/marry\n/divorce\n/adopt\n/leave\n/tree")


@dp.message(Command("marry"))
async def marry(msg: Message):
    if not msg.reply_to_message:
        return await msg.answer("Ответь на сообщение человека")
    
    user1 = msg.from_user.id
    user2 = msg.reply_to_message.from_user.id

    create_user(user1)
    create_user(user2)

    cursor.execute("UPDATE users SET partner_id=? WHERE user_id=?", (user2, user1))
    cursor.execute("UPDATE users SET partner_id=? WHERE user_id=?", (user1, user2))
    conn.commit()

    await msg.answer("💍 Вы теперь в браке!")


@dp.message(Command("divorce"))
async def divorce(msg: Message):
    user = msg.from_user.id
    cursor.execute("UPDATE users SET partner_id=NULL WHERE user_id=?", (user,))
    conn.commit()
    await msg.answer("💔 Развод...")


@dp.message(Command("adopt"))
async def adopt(msg: Message):
    if not msg.reply_to_message:
        return await msg.answer("Ответь на сообщение ребенка")

    parent = msg.from_user.id
    child = msg.reply_to_message.from_user.id

    create_user(parent)
    create_user(child)

    cursor.execute("UPDATE users SET parent_id=? WHERE user_id=?", (parent, child))
    conn.commit()

    await msg.answer("👶 Усыновление успешно!")


@dp.message(Command("leave"))
async def leave(msg: Message):
    user = msg.from_user.id
    cursor.execute("DELETE FROM users WHERE user_id=?", (user,))
    conn.commit()
    await msg.answer("🚪 Ты покинул семью")


def draw_tree(user_id):
    img = Image.new("RGB", (500, 500), "white")
    draw = ImageDraw.Draw(img)

    user = get_user(user_id)

    draw.text((200, 50), f"You: {user_id}", fill="black")

    if user and user[1]:
        draw.text((200, 150), f"Partner: {user[1]}", fill="blue")

    cursor.execute("SELECT user_id FROM users WHERE parent_id=?", (user_id,))
    children = cursor.fetchall()

    y = 250
    for child in children:
        draw.text((200, y), f"Child: {child[0]}", fill="green")
        y += 30

    path = f"tree_{user_id}.png"
    img.save(path)
    return path


@dp.message(Command("tree"))
async def tree(msg: Message):
    path = draw_tree(msg.from_user.id)
    await msg.answer_photo(types.FSInputFile(path))


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
