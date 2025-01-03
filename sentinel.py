import os
import hashlib
import asyncio
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.utils import executor
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Connect to PostgreSQL
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Create necessary tables
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS file_logs (
        id SERIAL PRIMARY KEY,
        sender_id BIGINT NOT NULL,
        sender_username TEXT,
        group_id BIGINT NOT NULL,
        group_name TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size BIGINT NOT NULL,
        file_hash TEXT UNIQUE NOT NULL,
        file_path TEXT NOT NULL,
        timestamp TIMESTAMPTZ DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS indexed_data (
        id SERIAL PRIMARY KEY,
        file_id INT REFERENCES file_logs(id) ON DELETE CASCADE,
        data_type TEXT NOT NULL,
        extracted_value TEXT NOT NULL,
        confidence_score FLOAT,
        timestamp TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_group_id ON file_logs (group_id);
    CREATE INDEX IF NOT EXISTS idx_sender_id ON file_logs (sender_id);
    CREATE INDEX IF NOT EXISTS idx_timestamp ON file_logs (timestamp);
    CREATE INDEX IF NOT EXISTS idx_extracted_value ON indexed_data (extracted_value);
    CREATE INDEX IF NOT EXISTS idx_data_type ON indexed_data (data_type);
    """)

    conn.commit()
    cur.close()
    conn.close()

create_tables()

# Function to calculate file hash
def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

# Function to extract and index data
def extract_and_index_data(file_id, file_path):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        extracted_data = []
        
        if file_path.endswith(".txt") or file_path.endswith(".csv"):
            df = pd.read_csv(file_path, delimiter=None, engine="python", error_bad_lines=False)
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        else:
            return

        for col in df.columns:
            for value in df[col].dropna().astype(str):
                if "@" in value and "." in value:
                    extracted_data.append(("email", value))
                elif len(value) > 8 and any(c.isdigit() for c in value):
                    extracted_data.append(("password", value))
                elif value.isalnum():
                    extracted_data.append(("username", value))

        for data_type, extracted_value in extracted_data:
            cur.execute(
                sql.SQL("INSERT INTO indexed_data (file_id, data_type, extracted_value) VALUES (%s, %s, %s)")
                .format(sql.Identifier("indexed_data")),
                (file_id, data_type, extracted_value),
            )

        conn.commit()
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    finally:
        cur.close()
        conn.close()

# Handle file messages
@dp.message_handler(content_types=[ContentType.DOCUMENT])
async def handle_docs(message: types.Message):
    document = message.document

    if document.mime_type not in ["text/plain", "text/csv", "application/json"]:
        return

    file_info = await bot.get_file(document.file_id)
    file_path = file_info.file_path
    local_file_path = f"downloads/{document.file_name}"

    os.makedirs("downloads", exist_ok=True)
    await bot.download_file(file_path, local_file_path)

    file_hash = calculate_hash(local_file_path)

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            sql.SQL("INSERT INTO file_logs (sender_id, sender_username, group_id, group_name, file_name, file_type, file_size, file_hash, file_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"),
            (
                message.from_user.id,
                message.from_user.username,
                message.chat.id,
                message.chat.title,
                document.file_name,
                document.mime_type,
                document.file_size,
                file_hash,
                local_file_path
            )
        )
        file_id = cur.fetchone()[0]
        conn.commit()

        await message.reply(f"✅ File saved! Processing: {document.file_name}")
        extract_and_index_data(file_id, local_file_path)

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        cur.close()
        conn.close()

# Search feature
@dp.message_handler(commands=["search"])
async def search_data(message: types.Message):
    query = message.get_args()

    if not query:
        await message.reply("Usage: /search <email/username/password>")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT file_id, data_type, extracted_value FROM indexed_data WHERE extracted_value ILIKE %s LIMIT 10;", (f"%{query}%",))
        results = cur.fetchall()

        if not results:
            await message.reply("No matches found.")
            return

        response = "🔍 **Search Results:**\n"
        for file_id, data_type, extracted_value in results:
            response += f"📁 File ID: {file_id}\n🔹 Type: {data_type}\n💾 Data: {extracted_value}\n\n"

        await message.reply(response)
    except Exception as e:
        await message.reply(f"Error in search: {e}")
    finally:
        cur.close()
        conn.close()

# Run the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)