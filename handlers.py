from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import db
from config import ADMINS, FLOWS, REQUIRED_VISITS
from wishes import get_random_wish

router = Router()

class RegistrationStates(StatesGroup):
    waiting_name = State()
    waiting_flow = State()

def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMINS

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "Добро пожаловать в бот учёта посещений физкультуры!\n\n"
        "Доступные команды:\n"
        "/register - Регистрация\n"
        "/info - Информация о посещениях\n"
    )
    if is_admin(message.from_user.id):
        await message.answer(
            "Команды администратора:\n"
            "/list - Список всех учеников\n"
            "/mark - Отметить посещение"
        )

@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext):
    """Start registration process."""
    student = await db.get_student(message.from_user.id)
    if student:
        await message.answer("Вы уже зарегистрированы!")
        return

    # Store command message ID
    await state.update_data(message_ids=[message.message_id])
    
    await state.set_state(RegistrationStates.waiting_name)
    name_msg = await message.answer("Пожалуйста, введите ваше ФИО:")
    # Store bot's message ID
    await state.update_data(message_ids=[message.message_id, name_msg.message_id])

@router.message(RegistrationStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Process student's name and ask for flow selection."""
    # Store user's message ID
    data = await state.get_data()
    message_ids = data.get('message_ids', []) + [message.message_id]
    
    # Validate name format (three words separated by spaces)
    name_parts = message.text.strip().split()
    if len(name_parts) != 3:
        msg = await message.answer(
            "Пожалуйста, введите ФИО в формате: Фамилия Имя Отчество\n"
            "Например: Иванов Иван Иванович"
        )
        await state.update_data(message_ids=message_ids + [msg.message_id])
        return

    await state.update_data(full_name=message.text, message_ids=message_ids)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=flow)] for flow in FLOWS],
        resize_keyboard=True
    )
    
    await state.set_state(RegistrationStates.waiting_flow)
    flow_msg = await message.answer(
        "Выберите ваш поток:",
        reply_markup=keyboard
    )
    # Store bot's message ID
    await state.update_data(message_ids=message_ids + [flow_msg.message_id])

@router.message(RegistrationStates.waiting_flow)
async def process_flow(message: Message, state: FSMContext):
    """Process flow selection and complete registration."""
    # Store user's message ID
    data = await state.get_data()
    message_ids = data.get('message_ids', []) + [message.message_id]
    
    if message.text not in FLOWS:
        msg = await message.answer("Пожалуйста, выберите поток из предложенных вариантов.")
        await state.update_data(message_ids=message_ids + [msg.message_id])
        return

    success = await db.register_student(
        message.from_user.id,
        data['full_name'],
        message.text
    )

    # Delete all registration messages
    for msg_id in message_ids:
        try:
            await message.bot.delete_message(message.chat.id, msg_id)
        except Exception:
            pass  # Ignore errors if message was already deleted

    await state.clear()
    if success:
        # Remove keyboard and send success message
        await message.answer(
            "Регистрация успешно завершена!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[]],
                resize_keyboard=True
            )
        )
        
        # Send attendance info
        student = await db.get_student(message.from_user.id)
        remaining = max(0, REQUIRED_VISITS - student['visits'])
        if remaining == 0:
            await message.answer("Поздравляем! Вы получили зачёт по физкультуре!")
        else:
            await message.answer(
                f"Количество посещений: {student['visits']}\n"
                f"До зачёта осталось: {remaining}"
            )
    else:
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")

@router.message(Command("info"))
async def cmd_info(message: Message):
    """Show student's attendance information."""
    student = await db.get_student(message.from_user.id)
    if not student:
        await message.answer("Вы не зарегистрированы. Используйте /register")
        return

    remaining = max(0, REQUIRED_VISITS - student['visits'])
    if remaining == 0:
        await message.answer("Поздравляем! Вы получили зачёт по физкультуре!")
    else:
        await message.answer(
            f"Количество посещений: {student['visits']}\n"
            f"До зачёта осталось: {remaining}"
        )

@router.message(Command("list"))
async def cmd_list(message: Message):
    """Show list of all students (admin only)."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    students = await db.get_all_students()
    if not students:
        await message.answer("Список учеников пуст.")
        return

    response = "Список учеников:\n\n"
    for student in students:
        response += (
            f"ID: {student['tg_id']}\n"
            f"ФИО: {student['full_name']}\n"
            f"Поток: {student['flow']}\n"
            f"Посещений: {student['visits']}\n\n"
        )
    
    await message.answer(response)

@router.message(Command("mark"))
async def cmd_mark(message: Message):
    """Show list of students for marking attendance (admin only)."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    students = await db.get_all_students()
    if not students:
        await message.answer("Список учеников пуст.")
        return

    # Create inline keyboard with student buttons
    keyboard = []
    for student in students:
        button_text = f"{student['full_name']} ({student['visits']}/{REQUIRED_VISITS})"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"mark_{student['tg_id']}"
            )
        ])

    await message.answer(
        "Выберите ученика для отметки посещения:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(lambda c: c.data.startswith('mark_'))
async def process_mark_callback(callback: CallbackQuery):
    """Process student selection for marking attendance."""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа к этой команде.", show_alert=True)
        return

    # Extract student ID from callback data
    student_id = int(callback.data.split('_')[1])
    
    # Mark attendance
    student = await db.increment_visits(student_id)
    if not student:
        await callback.answer("Ученик не найден.", show_alert=True)
        return

    # Calculate remaining visits
    remaining = max(0, REQUIRED_VISITS - student['visits'])
    status = (
        "Поздравляем! Вы получили зачёт по физкультуре!"
        if remaining == 0
        else f"До зачёта осталось: {remaining}"
    )

    # Get random wish
    wish = get_random_wish()

    # Notify the student
    await callback.bot.send_message(
        student_id,
        f"Отмечено посещение!\n"
        f"Количество посещений: {student['visits']}\n"
        f"{status}\n\n"
        f"{wish}"
    )

    # Update the message for admin
    await callback.message.edit_text(
        f"✅ Посещение отмечено для {student['full_name']}\n"
        f"Текущее количество: {student['visits']}/{REQUIRED_VISITS}"
    )
    await callback.answer() 