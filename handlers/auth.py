import string
import secrets
from pathlib import Path
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from werkzeug.security import check_password_hash, generate_password_hash

from config import UPLOAD_BASE
from database import get_user_by_username, add_user
from keyboards import main_menu
from states import AuthState, RegisterState

router = Router()
SESSIONS = {}


def user_id(message):
    return SESSIONS.get(message.from_user.id)


def generate_unique_folder_name(length: int = 10) -> str:
    # Алфавит из букв и цифр (62 символа), выбираем 10 НЕПОВТОРЯЮЩИХСЯ случайных символов
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.SystemRandom().sample(alphabet, length))


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if user_id(message):
        await message.answer("Главное меню:", reply_markup=main_menu())
        return
    await message.answer("Учебные файлы \n функционал сайта myfiles-kai.ru в telegram \n можете загружать и скачивать файлы также как и на сайте \n сайт и бот одна общая система - все файлы и учетные записи синхронизированы т.е. если вы зарегистрировались и загрузили файл на сайте вы можете пользоваться этим в боте и наоборот \n Используйте: \n /login - для входа \n /register для регистрации нового пользователя")


@router.message(Command("login"))
async def login(message: Message, state: FSMContext):
    await state.set_state(AuthState.username)
    await message.answer("Введите username:")


# --- РЕГИСТРАЦИЯ ---

@router.message(Command("register"))
async def register_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RegisterState.username)
    await message.answer("Регистрация новым пользователем.\nПридумайте username:")


@router.message(RegisterState.username)
async def register_username(message: Message, state: FSMContext):
    username = message.text.strip()
    if not username or len(username) < 3 or len(username) > 32:
        await message.answer("Имя пользователя должно быть от 3 до 32 символов. Попробуйте другое:")
        return

    # Проверка, занят ли username
    if get_user_by_username(username):
        await message.answer("Пользователь с таким именем уже существует. Введите другой username:")
        return

    await state.update_data(username=username)
    await state.set_state(RegisterState.password)
    await message.answer("Придумайте пароль:")


@router.message(RegisterState.password)
async def register_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 4:
        await message.answer("Пароль слишком короткий (минимум 4 символа). Попробуйте еще раз:")
        return

    await state.update_data(password=password)
    await state.set_state(RegisterState.confirm_password)
    await message.answer("Повторите пароль для подтверждения:")


@router.message(RegisterState.confirm_password)
async def register_confirm_password(message: Message, state: FSMContext):
    confirm_password = message.text.strip()
    data = await state.get_data()
    password = data.get("password")

    # Проверка на совпадение паролей
    if password != confirm_password:
        await message.answer("Пароли не совпадают! Введите пароль повторно:")
        await state.set_state(RegisterState.password)
        return

    username = data.get("username")
    password_hash = generate_password_hash(password)

    # Генерация 10 случайных неповторяющихся символов для папки
    random_folder = generate_unique_folder_name(10)
    folder_path = UPLOAD_BASE / random_folder

    try:
        # Создаем папку на диске
        folder_path.mkdir(parents=True, exist_ok=True)

        # Сохраняем в БД
        new_user_id = add_user(username, password_hash, str(folder_path))

        # Автоматический вход в систему
        SESSIONS[message.from_user.id] = new_user_id
        await state.clear()

        await message.answer(
            f"Успешная регистрация! Вы вошли как {username}.",
            reply_markup=main_menu()
        )
    except Exception as e:
        await state.clear()
        await message.answer("Произошла ошибка при регистрации. Попробуйте еще раз с помощью /register.")


# --- ВХОД В АККАУНТ ---

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