from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import get_text


def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz"),
        ]
    ])


def consent_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text(lang, "consent_agree"),
                callback_data="consent_yes"
            ),
        ],
        [
            InlineKeyboardButton(
                text=get_text(lang, "consent_disagree"),
                callback_data="consent_no"
            ),
        ],
    ])


def main_menu_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=get_text(lang, "btn_gad7"),
            callback_data="start_gad7"
        )],
        [InlineKeyboardButton(
            text=get_text(lang, "btn_phq9"),
            callback_data="start_phq9"
        )],
        [InlineKeyboardButton(
            text=get_text(lang, "btn_my_results"),
            callback_data="my_results"
        )],
        [
            InlineKeyboardButton(
                text=get_text(lang, "btn_change_lang"),
                callback_data="change_lang"
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_about"),
                callback_data="about"
            ),
        ],
    ])


def survey_answer_keyboard(lang: str, survey_type: str, question_idx: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"0 — {get_text(lang, 'answer_0')}",
            callback_data=f"ans_{survey_type}_{question_idx}_0"
        )],
        [InlineKeyboardButton(
            text=f"1 — {get_text(lang, 'answer_1')}",
            callback_data=f"ans_{survey_type}_{question_idx}_1"
        )],
        [InlineKeyboardButton(
            text=f"2 — {get_text(lang, 'answer_2')}",
            callback_data=f"ans_{survey_type}_{question_idx}_2"
        )],
        [InlineKeyboardButton(
            text=f"3 — {get_text(lang, 'answer_3')}",
            callback_data=f"ans_{survey_type}_{question_idx}_3"
        )],
    ])


def back_to_menu_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=get_text(lang, "btn_menu"),
            callback_data="main_menu"
        )]
    ])


# Админ-клавиатуры
def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📊 Статистика", callback_data="admin_stats"
        )],
        [InlineKeyboardButton(
            text="👥 Список пациентов", callback_data="admin_patients"
        )],
        [InlineKeyboardButton(
            text="🔍 Результаты пациента", callback_data="admin_patient_results"
        )],
        [InlineKeyboardButton(
            text="🚨 Оповещения", callback_data="admin_alerts"
        )],
    ])