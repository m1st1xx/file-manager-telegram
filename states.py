from aiogram.fsm.state import State, StatesGroup

class AuthState(StatesGroup):
    username = State()
    password = State()

class RegisterState(StatesGroup):
    username = State()
    password = State()
    confirm_password = State()

class SubjectState(StatesGroup):
    add_name = State()

class UploadState(StatesGroup):
    subject = State()