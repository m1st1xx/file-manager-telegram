from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile
from database import get_user_by_id, get_subjects, subject_exists
from keyboards import file_menu, main_menu, subjects_menu
from handlers.auth import SESSIONS
from config import UPLOAD_BASE, MAX_FILE_SIZE
from pathlib import Path
import re
import shutil

router = Router()

def safe_part(value):
    return value not in ("", ".", "..") and "\x00" not in value

def user_subject_path(user, subject):
    base = Path(user["folder_path"]).resolve()
    path = (base / subject).resolve()
    if not str(path).startswith(str(base) + str(Path("/"))):
        raise ValueError("invalid path")
    return path

def clean_filename(name):
    name = Path(name).name
    name = re.sub(r'[<>:"/\\\\|?*\\x00-\\x1f]', "_", name).strip()
    return name[:240]

@router.callback_query(F.data.startswith("download:subject:"))
async def list_download(cb: CallbackQuery):
    await list_files(cb, "download")

@router.callback_query(F.data.startswith("upload:subject:"))
async def list_upload(cb: CallbackQuery):
    await list_files(cb, "upload")

async def list_files(cb, mode):
    uid = SESSIONS.get(cb.from_user.id)
    user = get_user_by_id(uid)
    subject = cb.data.split(":", 2)[2]
    if not user or not subject_exists(uid, subject):
        return await cb.answer("Предмет не найден", show_alert=True)
    path = user_subject_path(user, subject)
    path.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in path.iterdir() if p.is_file()])
    if not files:
        text = f"«{subject}»\n\nФайлов нет."
    else:
        text = f"«{subject}»\n\n" + "\n".join(f"• {p.name}" for p in files)
    buttons = []
    for p in files:
        buttons.append([__import__("aiogram").types.InlineKeyboardButton(
            text=p.name[:50], callback_data=f"download:file:{subject}:{p.name}"
        )])
    if mode == "upload":
        buttons.append([__import__("aiogram").types.InlineKeyboardButton(text="📤 Загрузить файл", callback_data=f"upload_now:{subject}")])
    buttons.append([__import__("aiogram").types.InlineKeyboardButton(text="⬅️ Предметы", callback_data="upload_subjects" if mode=="upload" else "download_subjects")])
    await cb.message.edit_text(text, reply_markup=__import__("aiogram").types.InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("upload_now:"))
async def upload_now(cb: CallbackQuery, state: FSMContext):
    subject = cb.data.split(":", 1)[1]
    await state.update_data(subject=subject)
    await state.set_state("waiting_file")
    await cb.message.answer(f"Отправьте файл для «{subject}» как документ.")

@router.message(F.document)
async def receive_document(message: Message, state: FSMContext):
    if not SESSIONS.get(message.from_user.id):
        return
    data = await state.get_data()
    subject = data.get("subject")
    if not subject:
        return
    user = get_user_by_id(SESSIONS[message.from_user.id])
    if not user or not subject_exists(user["id"], subject):
        await state.clear()
        return await message.answer("Предмет не найден.")
    size = message.document.file_size or 0
    if size > MAX_FILE_SIZE:
        await state.clear()
        return await message.answer(f"Файл слишком большой. Лимит бота: {MAX_FILE_SIZE // (1024*1024)} МБ.")
    filename = clean_filename(message.document.file_name or "file")
    if not filename:
        await state.clear()
        return await message.answer("Некорректное имя файла.")
    path = user_subject_path(user, subject)
    path.mkdir(parents=True, exist_ok=True)
    destination = path / filename
    tg_file = await message.bot.get_file(message.document.file_id)
    await message.bot.download_file(tg_file.file_path, destination)
    await state.clear()
    await message.answer(f"Файл «{filename}» загружен.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("download:file:"))
async def download_file(cb: CallbackQuery):
    uid = SESSIONS.get(cb.from_user.id)
    user = get_user_by_id(uid)
    _, _, subject, filename = cb.data.split(":", 3)
    if not user or not subject_exists(uid, subject):
        return await cb.answer("Файл не найден", show_alert=True)
    path = user_subject_path(user, subject) / Path(filename).name
    if not path.is_file():
        return await cb.answer("Файл не найден", show_alert=True)
    await cb.answer()
    await cb.message.answer_document(FSInputFile(path))

@router.callback_query(F.data.startswith("delete:file:"))
async def delete_file(cb: CallbackQuery):
    uid = SESSIONS.get(cb.from_user.id)
    user = get_user_by_id(uid)
    _, _, subject, filename = cb.data.split(":", 3)
    if not user or not subject_exists(uid, subject):
        return await cb.answer("Файл не найден", show_alert=True)
    path = user_subject_path(user, subject) / Path(filename).name
    if path.is_file():
        path.unlink()
        await cb.answer("Удалено")
        await cb.message.answer(f"Файл «{path.name}» удалён.", reply_markup=main_menu())
    else:
        await cb.answer("Файл не найден", show_alert=True)
