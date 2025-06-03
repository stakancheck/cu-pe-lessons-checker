import aiosqlite
from config import DB_PATH

async def init_db():
    """Initialize database and create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE,
                full_name TEXT NOT NULL,
                flow TEXT NOT NULL,
                visits INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

async def register_student(tg_id: int, full_name: str, flow: str) -> bool:
    """Register a new student. Returns True if successful, False if already exists."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'INSERT INTO students (tg_id, full_name, flow) VALUES (?, ?, ?)',
                (tg_id, full_name, flow)
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False

async def get_student(tg_id: int) -> dict | None:
    """Get student information by Telegram ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT * FROM students WHERE tg_id = ?',
            (tg_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_all_students() -> list[dict]:
    """Get all registered students."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM students') as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def increment_visits(tg_id: int) -> dict | None:
    """Increment visits count for a student and return updated info."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            'UPDATE students SET visits = visits + 1 WHERE tg_id = ?',
            (tg_id,)
        )
        await db.commit()
        
        async with db.execute(
            'SELECT * FROM students WHERE tg_id = ?',
            (tg_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None 