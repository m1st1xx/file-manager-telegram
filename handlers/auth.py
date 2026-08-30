from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from werkzeug.security import check_password_hash
from database import get_user_by_username
from keyboards import main_menu
from states import AuthState

router = Router()
SESSIONS = {}

def user_id(message): return SESSIONS.get(message.from_user.id)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if user_id(message):
        await message.answer("Главное меню:", reply_markup=main_menu())
        return
    await state.set_state(AuthState.username)
    await message.answer("Введите username от вашего аккаунта сайта:")

@router.message(Command("login"))
async def login(message: Message, state: FSMContext):
    await state.set_state(AuthState.username)
    await message.answer("Введите username:")

@router.message(AuthState.username)
async def username(message: Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await state.set_state(AuthState.password)
    await message.answer("Введите пароль:")

@router.message(AuthState.password)
async def password(message: Message, state: FSMContext):
    data = await state.get_data()
    user = get_user_by_username(data["username"])
    if not user or not check_password_hash(user["password_hash"], message.text):
        await state.clear()
        await message.answer("Неверный username или пароль. Используйте /login для повторной попытки.")
        return
    SESSIONS[message.from_user.id] = user["id"]
    await state.clear()
    await message.answer(f"Добро пожаловать, {user['username']}!", reply_markup=main_menu())

@router.callback_query(F.data == "logout")
async def logout(callback: CallbackQuery):
    SESSIONS.pop(callback.from_user.id, None)
    await callback.answer("Вы вышли")
    await callback.message.answer("Вы вышли из аккаунта. /start — вход снова.")
