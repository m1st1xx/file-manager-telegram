from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from database import get_user_by_id, get_subjects, add_subject, delete_subject, subject_exists
from keyboards import subjects_menu, main_menu
from states import SubjectState
from handlers.auth import SESSIONS

router = Router()


def uid(cb):
    return SESSIONS.get(cb.from_user.id)


@router.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery):
    if not uid(cb):
        return await cb.answer("Сначала выполните /start", show_alert=True)
    await cb.message.edit_text("Главное меню:", reply_markup=main_menu())


@router.callback_query(F.data.in_({"subjects", "download_subjects", "upload_subjects"}))
async def show_subjects(cb: CallbackQuery):
    user = get_user_by_id(uid(cb))
    if not user:
        return await cb.answer("Сессия недействительна", show_alert=True)

    mode = "view"
    if cb.data == "download_subjects":
        mode = "download"
    if cb.data == "upload_subjects":
        mode = "upload"

    # Передаем список объектов из БД напрямую (содержат id и name)
    subjects = get_subjects(user["id"])

    if not subjects:
        await cb.message.edit_text("Предметов пока нет.", reply_markup=subjects_menu([], mode))
    else:
        await cb.message.edit_text("Выберите предмет:", reply_markup=subjects_menu(subjects, mode))


@router.callback_query(F.data == "subject:add")
async def add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(SubjectState.add_name)
    await cb.message.answer("Введите название предмета (до 100 символов):")


@router.message(SubjectState.add_name)
async def add_finish(message: Message, state: FSMContext):
    user = get_user_by_id(SESSIONS.get(message.from_user.id))
    name = " ".join(message.text.strip().split())
    if not user or not name or len(name) > 100 or "/" in name or "\\" in name or "\x00" in name:
        await message.answer("Некорректное название предмета.")
        return
    try:
        add_subject(user["id"], name)
        from pathlib import Path
        Path(user["folder_path"], name).mkdir(parents=True, exist_ok=True)
        await state.clear()
        await message.answer(f"Предмет «{name}» добавлен.", reply_markup=main_menu())
    except Exception:
        await message.answer("Такой предмет уже существует или произошла ошибка.")