from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import (
    get_stats, get_all_patients, get_patient_results,
    get_unread_alerts, mark_alerts_read
)
from keyboards import admin_keyboard
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return

    await message.answer(
        "🔐 <b>Админ-панель Qamqor</b>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    stats = await get_stats()

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Пациентов: <b>{stats['total_patients']}</b>\n"
        f"📋 Всего опросов: <b>{stats['total_surveys']}</b>\n"
        f"   ├ GAD-7: {stats['gad7_count']}\n"
        f"   └ PHQ-9: {stats['phq9_count']}\n"
        f"🚨 Непрочитанных оповещений: <b>{stats['unread_alerts']}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_patients")
async def admin_patients(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    patients = await get_all_patients()

    if not patients:
        await callback.message.edit_text(
            "👥 Пациентов пока нет.",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = "👥 <b>Список пациентов:</b>\n\n"
    for p in patients:
        text += (
            f"ID: <code>{p['patient_code']}</code> | "
            f"Язык: {p['language']} | "
            f"Дата: {p['registered_at'][:10]}\n"
        )

    if len(text) > 4000:
        text = text[:4000] + "\n\n... (список обрезан)"

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_patient_results")
async def admin_patient_results_prompt(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    await callback.message.edit_text(
        "🔍 Введите ID пациента (например: <code>0001</code>):\n\n"
        "Отправьте команду: /results 0001",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("results"))
async def cmd_results(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используйте: /results 0001")
        return

    patient_code = parts[1]
    results = await get_patient_results(patient_code)

    if not results:
        await message.answer(
            f"📭 Результатов для пациента <code>{patient_code}</code> не найдено.",
            parse_mode="HTML"
        )
        return

    text = f"📈 <b>Результаты пациента {patient_code}:</b>\n\n"

    for r in results:
        text += (
            f"📋 <b>{r['survey_type']}</b> — {r['completed_at'][:16]}\n"
            f"   Баллы: {r['total_score']} | Уровень: {r['level']}\n"
            f"   Ответы: {r['answers']}\n\n"
        )

    if len(text) > 4000:
        text = text[:4000] + "\n\n... (обрезано)"

    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "admin_alerts")
async def admin_alerts(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    alerts = await get_unread_alerts()

    if not alerts:
        await callback.message.edit_text(
            "✅ Нет новых оповещений.",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = "🚨 <b>Оповещения:</b>\n\n"

    for a in alerts:
        text += (
            f"⚠️ Пациент <code>{a['patient_code']}</code>\n"
            f"   Тип: {a['alert_type']}\n"
            f"   Ответ: {a['question_answer']}\n"
            f"   Дата: {a['created_at'][:16]}\n\n"
        )

    if len(text) > 4000:
        text = text[:4000] + "\n... (обрезано)"

    await mark_alerts_read()

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()