from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать файлы", callback_data="download_subjects")],
        [InlineKeyboardButton(text="📤 Загрузить файл", callback_data="upload_subjects")],
        [InlineKeyboardButton(text="📚 Предметы", callback_data="subjects")],
        [InlineKeyboardButton(text="🚪 Выйти", callback_data="logout")],
    ])

def subjects_menu(subjects, mode="view"):
    rows = []
    for s in subjects:
        rows.append([InlineKeyboardButton(text=s["name"], callback_data=f"{mode}:subj:{s['id']}")])
    rows.append([InlineKeyboardButton(text="➕ Добавить предмет", callback_data="subject:add")])
    rows.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def file_menu(subject_id, file_idx, mode):
    rows = []
    if mode in ("download", "view"):
        rows.append([InlineKeyboardButton(text="📥 Скачать", callback_data=f"dl:f:{subject_id}:{file_idx}")])
    rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del:f:{subject_id}:{file_idx}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{mode}:subj:{subject_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)