import os
import hashlib
import logging
import psycopg2
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL Database Configuration
DB_PARAMS = {
    "dbname": "sentinel_db",
    "user": "postgres",
    "password": "yourpassword",
    "host": "localhost",
    "port": "5432"
}

def db_connect():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return None

def create_table():
    """Create table if it doesn't exist"""
    conn = db_connect()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_logs (
                id SERIAL PRIMARY KEY,
                sender_id BIGINT NOT NULL,
                sender_username TEXT,
                group_id BIGINT NOT NULL,
                group_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size BIGINT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        conn.commit()
        cursor.close()
        conn.close()

def generate_file_hash(file_path):
    """Generate SHA-256 hash of the file content"""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

async def start(update: Update, context):
    await update.message.reply_text("SentinelBot is active. I will monitor this group for .txt files.")

async def handle_file(update: Update, context):
    """Handles document uploads"""
    if update.message.document and update.message.document.mime_type == "text/plain":
        document = update.message.document
        sender = update.message.from_user
        chat = update.message.chat

        file_id = document.file_id
        file_name = document.file_name
        file_size = document.file_size

        # Download the file temporarily
        temp_path = f"/tmp/{file_name}"
        file = await context.bot.get_file(file_id)
        await file.download_to_drive(temp_path)

        # Generate file hash (to avoid duplicates)
        file_hash = generate_file_hash(temp_path)

        # Define structured storage path
        date_folder = datetime.now().strftime("%Y-%m-%d")
        group_folder = chat.title.replace(" ", "_")  # Replace spaces with underscores
        save_dir = f"data/{date_folder}/{group_folder}"
        os.makedirs(save_dir, exist_ok=True)

        # Save file with its hash as the name
        save_path = f"{save_dir}/{file_hash}.txt"
        os.rename(temp_path, save_path)

        # Store metadata in PostgreSQL
        conn = db_connect()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO file_logs (sender_id, sender_username, group_id, group_name, 
                    file_name, file_size, file_hash, file_id, file_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (file_hash) DO NOTHING;
                    """,
                    (
                        sender.id,
                        sender.username,
                        chat.id,
                        chat.title,
                        file_name,
                        file_size,
                        file_hash,
                        file_id,
                        save_path
                    )
                )
                conn.commit()
            except Exception as e:
                logger.error(f"Database insertion failed: {e}")
            finally:
                cursor.close()
                conn.close()
        
        await update.message.reply_text(f"📁 File '{file_name}' saved and logged.")

async def error_handler(update: object, context):
    """Handles errors globally."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    create_table()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_error_handler(error_handler)

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()