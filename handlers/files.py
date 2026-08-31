from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_by_id, get_subject_by_id, subject_exists
from keyboards import main_menu, file_menu
from handlers.auth import SESSIONS
from config import UPLOAD_BASE, MAX_FILE_SIZE
from pathlib import Path
import re

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
    return name[:100]


@router.callback_query(F.data.startswith("download:subj:"))
async def list_download(cb: CallbackQuery):
    await list_files(cb, "download")


@router.callback_query(F.data.startswith("upload:subj:"))
async def list_upload(cb: CallbackQuery):
    await list_files(cb, "upload")


@router.callback_query(F.data.startswith("view:subj:"))
async def list_view(cb: CallbackQuery):
    await list_files(cb, "view")


async def list_files(cb, mode):
    uid = SESSIONS.get(cb.from_user.id)
    user = get_user_by_id(uid)
    subject_id = int(cb.data.split(":", 2)[2])
    subject_row = get_subject_by_id(uid, subject_id)
    if not user or not subject_row:
        return await cb.answer("Предмет не найден", show_alert=True)

    subject = subject_row["name"]
    path = user_subject_path(user, subject)
    path.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in path.iterdir() if p.is_file()])

    if not files:
        text = f"«{subject}»\n\nФайлов нет."
    else:
        text = f"«{subject}»\n\n" + "\n".join(f"• {p.name}" for p in files)

    buttons = []
    for idx, p in enumerate(files):
        btn_text = p.name if len(p.name) <= 40 else p.name[:37] + "..."
        # Нажатие на файл открывает меню действий (fi:subject_id:file_idx:mode)
        buttons.append([InlineKeyboardButton(
            text=btn_text, callback_data=f"fi:{subject_id}:{idx}:{mode}"
        )])

    if mode == "upload":
        buttons.append([InlineKeyboardButton(text="📤 Загрузить файл", callback_data=f"upload_now:{subject_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Предметы",
                                         callback_data="upload_subjects" if mode == "upload" else "download_subjects")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# Открытие меню управления выбранным файлом
@router.callback_query(F.data.startswith("fi:"))
async def show_file_options(cb: CallbackQuery):
    uid = SESSIONS.get(cb.from_user.id)
    user = get_user_by_id(uid)
    _, subject_id_str, file_idx_str, mode = cb.data.split(":")
    subject_id, file_idx = int(subject_id_str), int(file_idx_str)

    subject_row = get_subject_by_id(uid, subject_id)
    if not user or not subject_row:
        return await cb.answer("Файл не найден", show_alert=True)

    subject = subject_row["name"]
    path = user_subject_path(user, subject)
    files = sorted([p for p in path.iterdir() if p.is_file()])

    if file_idx < 0 or file_idx >= len(files):
        return await cb.answer("Файл не найден", show_alert=True)

    file_path = files[file_idx]
    text = f"📄 **Файл:** {file_path.name}\n📚 **Предмет:** {subject}"
    await cb.message.edit_text(text, reply_markup=file_menu(subject_id, file_idx, mode))


@router.callback_query(F.data.startswith("upload_now:"))
async def upload_now(cb: CallbackQuery, state: FSMContext):
    uid = SESSIONS.get(cb.from_user.id)
    subject_id = int(cb.data.split(":", 1)[1])
    subject_row = get_subject_by_id(uid, subject_id)
    if not subject_row:
        return await cb.answer("Предмет не найден", show_alert=True)

    await state.update_data(subject=subject_row["name"])
    await state.set_state("waiting_file")
    await cb.message.answer(f"Отправьте файл для «{subject_row['name']}» как документ.")


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
        return await message.answer(f"Файл слишком большой. Лимит бота: {MAX_FILE_SIZE // (1024 * 1024)} МБ.")
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


@router.callback_query(F.data.startswith("dl:f:"))
async def download_file(cb: CallbackQuery):
    uid = SESSIONS.get(cb.from_user.id)
    user = get_user_by_id(uid)
    parts = cb.data.split(":")
    subject_id = int(parts[2])
    file_idx = int(parts[3])

    subject_row = get_subject_by_id(uid, subject_id)
    if not user or not subject_row:
        return await cb.answer("Файл не найден", show_alert=True)

    subject = subject_row["name"]
    path = user_subject_path(user, subject)
    files = sorted([p for p in path.iterdir() if p.is_file()])

    if file_idx < 0 or file_idx >= len(files):
        return await cb.answer("Файл не найден", show_alert=True)

    file_path = files[file_idx]
    if not file_path.is_file():
        return await cb.answer("Файл не найден", show_alert=True)

    await cb.answer()
    await cb.message.answer_document(FSInputFile(file_path))
    await cb.message.answer(f"Файл «{file_path.name}» загружен.", reply_markup=main_menu())


@router.callback_query(F.data.startswith("del:f:"))
async def delete_file(cb: CallbackQuery):
    uid = SESSIONS.get(cb.from_user.id)
    user = get_user_by_id(uid)
    parts = cb.data.split(":")
    subject_id = int(parts[2])
    file_idx = int(parts[3])

    subject_row = get_subject_by_id(uid, subject_id)
    if not user or not subject_row:
        return await cb.answer("Файл не найден", show_alert=True)

    subject = subject_row["name"]
    path = user_subject_path(user, subject)
    files = sorted([p for p in path.iterdir() if p.is_file()])

    if file_idx < 0 or file_idx >= len(files):
        return await cb.answer("Файл не найден", show_alert=True)

    file_path = files[file_idx]
    if file_path.is_file():
        filename = file_path.name
        file_path.unlink()
        await cb.answer("Удалено")
        await cb.message.answer(f"Файл «{filename}» удалён.", reply_markup=main_menu())
    else:
        await cb.answer("Файл не найден", show_alert=True)