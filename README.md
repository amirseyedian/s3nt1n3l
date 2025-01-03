📜 README.md

📌 Telegram Cyber Threat Intelligence Bot

This bot monitors Telegram groups & channels, collects files (.txt, .csv, .json), extracts metadata & credentials, and makes them searchable in a PostgreSQL database.

🚀 Features

✅ Monitors Telegram Groups: Saves shared files automatically
✅ Stores File Metadata: Saves sender info, group details, file type & size
✅ Extracts Credentials & PII: Detects emails, usernames, and passwords
✅ Indexes Data for Search: Enables quick lookup of leaked credentials
✅ Fast Search API: /search <query> to find extracted credentials

📂 Project Structure

📁 telegram-cti-bot
│-- 📜 bot.py # Main Telegram bot script
│-- 📜 .env # Stores bot token & database credentials
│-- 📜 requirements.txt # Required dependencies
│-- 📜 README.md # Documentation
│-- 📁 downloads # Directory where files are saved

🔧 Requirements
• Python 3.8+
• PostgreSQL
• Telegram Bot API Token
• Pandas for data parsing

Install dependencies:

pip install -r requirements.txt

⚙️ Configuration

1️⃣ Set up PostgreSQL database
Run the following SQL commands to create required tables:

CREATE TABLE file_logs (
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

CREATE TABLE indexed_data (
id SERIAL PRIMARY KEY,
file_id INT REFERENCES file_logs(id) ON DELETE CASCADE,
data_type TEXT NOT NULL,
extracted_value TEXT NOT NULL,
timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_group_id ON file_logs (group_id);
CREATE INDEX idx_extracted_value ON indexed_data (extracted_value);

2️⃣ Set up the .env file

TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:password@localhost/dbname

▶️ Running the Bot

Run the bot with:

python bot.py

🔍 Usage
• Add the bot to Telegram groups.
• It will automatically save files and index credentials.
• Use the /search command to find leaked credentials.

/search example@email.com

📌 Future Improvements

🔹 AI-based PII detection (e.g., named entity recognition)
🔹 Enhanced file parsing (PDF, Word documents, etc.)
🔹 Improved security (Restrict bot access)

🤝 Contribution

Feel free to fork, modify, or suggest improvements!

💡 Need Help?

Contact the developer or open an issue on GitHub. 🚀
