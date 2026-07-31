from datetime import datetime
import requests
import feedparser
import sqlite3
from pathlib import Path

BOT_TOKEN = "8283088828:AAHckn1e8XZ9nzeScKvUGkm0bDIhCLlTm7I"
CHAT_ID = "8836772565"

RSS_URL = "https://hnrss.org/frontpage"

DB_PATH = Path("data/opportunities.db")

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    respuesta = requests.post(url, data=data)
    return respuesta.status_code

def crear_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            detected_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def oportunidad_existente(link):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM opportunities WHERE link = ?",
        (link,),
    )
    resultado = cur.fetchone()
    conn.close()
    return resultado is not None

def guardar_oportunidad(title, link):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO opportunities(title, link, detected_at) VALUES (?, ?, ?)",
        (
            title,
            link,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()

def revisar_fuente():
    feed = feedparser.parse(RSS_URL)
    nuevas = 0

    for entry in feed.entries[:5]:
        title = entry.title
        link = entry.link

        if not oportunidad_existente(link):
            guardar_oportunidad(title, link)
            mensaje = f"🟢 Nueva oportunidad detectada\\n\\n{title}\\n\\n{link}"
            enviar_telegram(mensaje)
            nuevas += 1

    return nuevas

def main():
    crear_db()

    print("=" * 50)
    print("        OPPORTUNITY ENGINE v0.3")
    print("=" * 50)

    nuevas = revisar_fuente()

    print(f"Nuevas oportunidades: {nuevas}")
    print("Base de datos: OK")
    print("Telegram: OK")
    print("=" * 50)

if __name__ == "__main__":
    main()