from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import get_patient, register_patient, update_language, get_patient_language
from keyboards import (
    language_keyboard, consent_keyboard,
    main_menu_keyboard, back_to_menu_keyboard
)
from texts import get_text

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    patient = await get_patient(message.from_user.id)
    if patient:
        lang = patient["language"]
        code = patient["patient_code"]
        await message.answer(
            get_text(lang, "main_menu").format(code=code),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            get_text("ru", "choose_language"),
            reply_markup=language_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("lang_"))
async def choose_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]

    patient = await get_patient(callback.from_user.id)
    if patient:
        await update_language(callback.from_user.id, lang)
        code = patient["patient_code"]
        await callback.message.edit_text(
            get_text(lang, "main_menu").format(code=code),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML"
        )
    else:
        # Новый пользователь — показываем приветствие и согласие
        await callback.message.edit_text(
            get_text(lang, "welcome"),
            parse_mode="HTML"
        )
        await callback.message.answer(
            get_text(lang, "consent_text"),
            reply_markup=consent_keyboard(lang),
            parse_mode="HTML"
        )

    # Сохраняем язык временно в state (или через callback data)
    await callback.answer()


@router.callback_query(F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery):
    # Определяем язык по тексту кнопки
    lang = "kz" if "Келісемін" in callback.message.text else "ru"

    patient = await get_patient(callback.from_user.id)
    if patient:
        code = patient["patient_code"]
        await callback.message.edit_text(
            get_text(lang, "already_registered").format(code=code),
            parse_mode="HTML"
        )
    else:
        code = await register_patient(callback.from_user.id, lang)
        await callback.message.edit_text(
            get_text(lang, "registered").format(code=code),
            parse_mode="HTML"
        )
        await callback.message.answer(
            get_text(lang, "main_menu").format(code=code),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data == "consent_no")
async def consent_no(callback: CallbackQuery):
    # Пробуем определить язык
    lang = "kz" if "Келіспеймін" in (callback.message.text or "") else "ru"
    await callback.message.edit_text(
        get_text(lang, "consent_declined"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    patient = await get_patient(callback.from_user.id)
    if not patient:
        await callback.message.edit_text("Нажмите /start для начала.")
        await callback.answer()
        return

    lang = patient["language"]
    code = patient["patient_code"]
    await callback.message.edit_text(
        get_text(lang, "main_menu").format(code=code),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "change_lang")
async def change_lang(callback: CallbackQuery):
    await callback.message.edit_text(
        get_text("ru", "choose_language"),
        reply_markup=language_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    lang = await get_patient_language(callback.from_user.id)
    await callback.message.edit_text(
        get_text(lang, "about"),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()