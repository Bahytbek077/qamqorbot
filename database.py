import aiosqlite
import asyncio
from datetime import datetime
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                patient_code TEXT UNIQUE NOT NULL,
                language TEXT DEFAULT 'ru',
                consent_given INTEGER DEFAULT 0,
                registered_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS survey_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                survey_type TEXT NOT NULL,
                answers TEXT NOT NULL,
                total_score INTEGER NOT NULL,
                level TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY (telegram_id) REFERENCES patients(telegram_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                patient_code TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                question_answer INTEGER,
                created_at TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def register_patient(telegram_id: int, language: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT patient_code FROM patients WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]

        cursor = await db.execute("SELECT COUNT(*) FROM patients")
        count = (await cursor.fetchone())[0]
        patient_code = f"{count + 1:04d}"

        await db.execute(
            """INSERT INTO patients (telegram_id, patient_code, language, consent_given, registered_at)
               VALUES (?, ?, ?, 1, ?)""",
            (telegram_id, patient_code, language, datetime.now().isoformat())
        )
        await db.commit()
        return patient_code


async def get_patient(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM patients WHERE telegram_id = ?",
            (telegram_id,)
        )
        return await cursor.fetchone()


async def get_patient_language(telegram_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT language FROM patients WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else "ru"


async def update_language(telegram_id: int, language: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE patients SET language = ? WHERE telegram_id = ?",
            (language, telegram_id)
        )
        await db.commit()


async def save_survey_result(telegram_id: int, survey_type: str,
                              answers: list, total_score: int, level: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO survey_results 
               (telegram_id, survey_type, answers, total_score, level, completed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, survey_type, str(answers), total_score, level,
             datetime.now().isoformat())
        )
        await db.commit()


async def save_alert(telegram_id: int, patient_code: str,
                     alert_type: str, question_answer: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO alerts 
               (telegram_id, patient_code, alert_type, question_answer, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (telegram_id, patient_code, alert_type, question_answer,
             datetime.now().isoformat())
        )
        await db.commit()


async def get_all_patients():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM patients ORDER BY id"
        )
        return await cursor.fetchall()


async def get_patient_results(patient_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT sr.* FROM survey_results sr
               JOIN patients p ON sr.telegram_id = p.telegram_id
               WHERE p.patient_code = ?
               ORDER BY sr.completed_at DESC""",
            (patient_code,)
        )
        return await cursor.fetchall()


async def get_unread_alerts():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM alerts WHERE is_read = 0 ORDER BY created_at DESC"
        )
        return await cursor.fetchall()


async def mark_alerts_read():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE alerts SET is_read = 1")
        await db.commit()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM patients")
        total_patients = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM survey_results")
        total_surveys = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM survey_results WHERE survey_type = 'GAD7'"
        )
        gad7_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM survey_results WHERE survey_type = 'PHQ9'"
        )
        phq9_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM alerts WHERE is_read = 0"
        )
        unread_alerts = (await cursor.fetchone())[0]

        return {
            "total_patients": total_patients,
            "total_surveys": total_surveys,
            "gad7_count": gad7_count,
            "phq9_count": phq9_count,
            "unread_alerts": unread_alerts
        }