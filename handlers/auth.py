from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
import re
import database
from states import AuthState, Register
from keyboards import main_menu

router = Router()

def valid_username(x):
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", x))

@router.startup()
async def startup():
    database.init()

@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    u = database.user_by_telegram(m.from_user.id)
    if u:
        await m.answer(f"Вы вошли как {u['username']}.", reply_markup=main_menu())
    else:
        await m.answer("Добро пожаловать! /register — регистрация, /login — вход.")

@router.message(Command("register"))
async def register(m: Message, state: FSMContext):
    if database.user_by_telegram(m.from_user.id):
        await m.answer("Этот Telegram уже привязан к аккаунту.")
        return
    await state.clear()
    await state.set_state(Register.username)
    await m.answer("Введите username (3–32 символа: латиница, цифры, _, -, .):")

@router.message(Register.username)
async def reg_username(m: Message, state: FSMContext):
    x = m.text.strip()
    if not valid_username(x):
        await m.answer("Некорректный username.")
        return
    if database.username_taken(x):
        await m.answer("Такой username уже занят.")
        return
    await state.update_data(username=x)
    await state.set_state(Register.password)
    await m.answer("Введите пароль (минимум 6 символов):")

@router.message(Register.password)
async def reg_password(m: Message, state: FSMContext):
    if len(m.text) < 6:
        await m.answer("Пароль должен быть не короче 6 символов.")
        return
    await state.update_data(password=m.text)
    await state.set_state(Register.confirm)
    await m.answer("Повторите пароль:")

@router.message(Register.confirm)
async def reg_confirm(m: Message, state: FSMContext):
    data = await state.get_data()
    if m.text != data["password"]:
        await m.answer("Пароли не совпадают. Введите пароль ещё раз.")
        await state.set_state(Register.password)
        return

    username = data["username"]
    folder = str(Path("/app/uploads") / username)

    try:
        Path(folder).mkdir(parents=True, exist_ok=True)
        uid = database.create_user(
            username,
            generate_password_hash(m.text),
            folder,
            m.from_user.id
        )
    except Exception:
        await m.answer("Не удалось создать аккаунт. Возможно, username уже занят.")
        return

    await state.clear()
    await m.answer(
        f"Регистрация завершена. Аккаунт «{username}» можно использовать и на сайте.",
        reply_markup=main_menu()
    )

@router.message(Command("login"))
async def login(m: Message, state: FSMContext):
    if database.user_by_telegram(m.from_user.id):
        await m.answer("Вы уже вошли.", reply_markup=main_menu())
        return
    await state.clear()
    await state.set_state(AuthState.username)
    await m.answer("Введите username:")

@router.message(AuthState.username)
async def login_user(m: Message, state: FSMContext):
    await state.update_data(username=m.text.strip())
    await state.set_state(AuthState.password)
    await m.answer("Введите пароль:")

@router.message(AuthState.password)
async def login_pass(m: Message, state: FSMContext):
    d = await state.get_data()
    u = database.user_by_username(d["username"])
    if not u or not check_password_hash(u["password_hash"], m.text):
        await state.clear()
        await m.answer("Неверные данные. /login для повтора.")
        return
    database.link_telegram(u["id"], m.from_user.id)
    await state.clear()
    await m.answer(f"Вы вошли как {u['username']}.", reply_markup=main_menu())

@router.callback_query(F.data == "logout")
async def logout(c: CallbackQuery):
    u = database.user_by_telegram(c.from_user.id)
    if u:
        database.link_telegram(u["id"], None)
    await c.answer("Вы вышли")
    await c.message.answer("Вы вышли. /login или /start для входа.")
