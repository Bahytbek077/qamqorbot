from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import (
    get_patient, get_patient_language, save_survey_result,
    save_alert, get_patient_results
)
from keyboards import (
    survey_answer_keyboard, back_to_menu_keyboard, main_menu_keyboard
)
from texts import get_text, TEXTS
from config import ADMIN_IDS

router = Router()

# Хранилище текущих ответов (в памяти, для демо достаточно)
user_surveys: dict = {}


def get_gad7_level(score: int) -> str:
    if score <= 4:
        return "minimal"
    elif score <= 9:
        return "mild"
    elif score <= 14:
        return "moderate"
    else:
        return "severe"


def get_phq9_level(score: int) -> str:
    if score <= 4:
        return "minimal"
    elif score <= 9:
        return "mild"
    elif score <= 14:
        return "moderate"
    elif score <= 19:
        return "moderately_severe"
    else:
        return "severe"


async def send_question(callback: CallbackQuery, survey_type: str,
                        question_idx: int, lang: str):
    questions_key = f"{survey_type.lower()}_questions"
    questions = get_text(lang, questions_key)
    total = len(questions)

    intro_key = f"{survey_type.lower()}_intro"
    intro = get_text(lang, intro_key).format(current=question_idx + 1, total=total)

    question_text = questions[question_idx]

    await callback.message.edit_text(
        f"{intro}\n\n<b>{question_text}</b>",
        reply_markup=survey_answer_keyboard(lang, survey_type.lower(), question_idx),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "start_gad7")
async def start_gad7(callback: CallbackQuery):
    patient = await get_patient(callback.from_user.id)
    if not patient:
        await callback.answer("Нажмите /start", show_alert=True)
        return

    lang = patient["language"]
    user_id = callback.from_user.id
    user_surveys[user_id] = {"type": "GAD7", "answers": [], "lang": lang}

    await send_question(callback, "GAD7", 0, lang)
    await callback.answer()


@router.callback_query(F.data == "start_phq9")
async def start_phq9(callback: CallbackQuery):
    patient = await get_patient(callback.from_user.id)
    if not patient:
        await callback.answer("Нажмите /start", show_alert=True)
        return

    lang = patient["language"]
    user_id = callback.from_user.id
    user_surveys[user_id] = {"type": "PHQ9", "answers": [], "lang": lang}

    await send_question(callback, "PHQ9", 0, lang)
    await callback.answer()


@router.callback_query(F.data.startswith("ans_"))
async def handle_answer(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    if user_id not in user_surveys:
        await callback.answer("Сессия истекла. Начните заново.", show_alert=True)
        return

    parts = callback.data.split("_")
    # ans_gad7_0_2 -> survey=gad7, q_idx=0, answer=2
    survey_type_lower = parts[1]
    question_idx = int(parts[2])
    answer_value = int(parts[3])

    survey_data = user_surveys[user_id]
    lang = survey_data["lang"]
    survey_type = survey_data["type"]

    # Проверяем что отвечаем на правильный вопрос
    expected_idx = len(survey_data["answers"])
    if question_idx != expected_idx:
        await callback.answer()
        return

    survey_data["answers"].append(answer_value)

    questions_key = f"{survey_type_lower}_questions"
    questions = get_text(lang, questions_key)
    total = len(questions)

    # PHQ-9, вопрос 9 (индекс 8) — проверка на суицидальные мысли
    if survey_type == "PHQ9" and question_idx == 8 and answer_value >= 2:
        patient = await get_patient(user_id)
        if patient:
            await save_alert(
                user_id, patient["patient_code"],
                "PHQ9_Q9_HIGH", answer_value
            )
            # Оповещение админам
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"🚨 <b>ВНИМАНИЕ!</b>\n\n"
                        f"Пациент <code>{patient['patient_code']}</code>\n"
                        f"PHQ-9, вопрос 9 (суицидальные мысли)\n"
                        f"Ответ: <b>{answer_value}</b> из 3\n\n"
                        f"Требуется внимание специалиста!",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    next_idx = question_idx + 1

    if next_idx < total:
        await send_question(callback, survey_type, next_idx, lang)
    else:
        # Опрос завершён
        total_score = sum(survey_data["answers"])

        if survey_type == "GAD7":
            level_key = get_gad7_level(total_score)
            level_text = get_text(lang, "gad7_levels")[level_key]
            recommendation = get_text(lang, "gad7_recommendations")[level_key]
        else:
            level_key = get_phq9_level(total_score)
            level_text = get_text(lang, "phq9_levels")[level_key]
            recommendation = get_text(lang, "phq9_recommendations")[level_key]

        # Сохраняем в БД
        await save_survey_result(
            user_id, survey_type,
            survey_data["answers"], total_score, level_key
        )

        # Формируем ответ
        result_text = get_text(lang, "survey_complete").format(
            level=level_text,
            recommendation=recommendation,
            general_wish=get_text(lang, "general_wish")
        )

        # Если PHQ-9 Q9 высокий — добавляем предупреждение
        if survey_type == "PHQ9" and survey_data["answers"][8] >= 2:
            result_text += "\n\n" + get_text(lang, "phq9_q9_alert")

        await callback.message.edit_text(
            result_text,
            reply_markup=back_to_menu_keyboard(lang),
            parse_mode="HTML"
        )

        # Очищаем данные сессии
        del user_surveys[user_id]

    await callback.answer()


@router.callback_query(F.data == "my_results")
async def my_results(callback: CallbackQuery):
    patient = await get_patient(callback.from_user.id)
    if not patient:
        await callback.answer("Нажмите /start", show_alert=True)
        return

    lang = patient["language"]
    code = patient["patient_code"]
    results = await get_patient_results(code)

    if not results:
        await callback.message.edit_text(
            get_text(lang, "no_results"),
            reply_markup=back_to_menu_keyboard(lang),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = get_text(lang, "results_header")

    for r in results[:10]:  # последние 10
        survey_type = r["survey_type"]
        date = r["completed_at"][:10]
        level_key = r["level"]

        if survey_type == "GAD7":
            level_text = get_text(lang, "gad7_levels").get(level_key, level_key)
        else:
            level_text = get_text(lang, "phq9_levels").get(level_key, level_key)

        text += get_text(lang, "result_item").format(
            survey_type=survey_type,
            date=date,
            level=level_text
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()