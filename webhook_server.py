# --- Webhook Server pro proaktivní spuštění Vendy ---
# FastAPI endpoint, který přijme telegram_id a zahájí konverzaci

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

import runtime
from tools.sea_database import get_initial_state

load_dotenv()

app = FastAPI(title="Vendy Webhook Server")

# Pydantic model pro request body
class WebhookStartRequest(BaseModel):
    telegram_id: str


def extract_bot_reply(result: dict) -> str:
    """
    Extrahuje textovou odpověď z výsledku grafu.
    Gemini 2.5 často vrací obsah jako list objektů místo čistého stringu.
    """
    last_msg = result["messages"][-1]
    
    if isinstance(last_msg.content, list):
        parts = []
        for item in last_msg.content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts)
    else:
        return last_msg.content


async def send_telegram_message(chat_id: str, text: str) -> bool:
    """
    Odešle zprávu přes Telegram Bot API.
    Vrací True pokud se podařilo, jinak False.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Zpráva odeslána na Telegram (chat_id: {chat_id})")
            return True
        else:
            print(f"❌ Chyba při odesílání na Telegram: {response.text}")
            return False


@app.post("/webhook/start")
async def webhook_start(request: WebhookStartRequest):
    """
    Webhook endpoint pro zahájení konverzace s kandidátem.
    
    Přijme telegram_id, načte data ze SeaTable, spustí graf
    a proaktivně pošle úvodní zprávu kandidátovi.
    """
    telegram_id = request.telegram_id
    print(f"🔔 Webhook přijat pro telegram_id: {telegram_id}")
    
    # 1. Ověření, že je graf inicializován
    if runtime.graph is None:
        raise HTTPException(
            status_code=503, 
            detail="Graf není inicializován. Aplikace se stále spouští."
        )
    
    # 2. Konfigurace pro graf
    config = {"configurable": {"thread_id": telegram_id}}
    
    # 3. Inicializace ze SeaTable
    print(f"🔍 Inicializace: Tahám data ze SeaTable pro ID {telegram_id}...")
    initial_db_data = get_initial_state(telegram_id)
    
    if not initial_db_data:
        raise HTTPException(
            status_code=404,
            detail=f"Kandidát s telegram_id {telegram_id} nebyl nalezen v SeaTable"
        )
    
    # 4. Spuštění grafu s trigger zprávou
    # Použijeme speciální systémovou zprávu, která signalizuje proaktivní zahájení
    inputs = {
        "messages": [("user", "[SYSTEM: Zahájit konverzaci - kandidát právě dokončil registraci]")],
        "row_id": initial_db_data["row_id"],
        "status": initial_db_data["status"],
        "candidate_data": initial_db_data["candidate_data"],
        "corrected_info": initial_db_data["corrected_info"],
    }
    
    print(f"🚀 Spouštím graf pro kandidáta: {initial_db_data['candidate_data'].get('full_name', 'neznámý')}")
    
    # 5. Invoke grafu
    result = runtime.graph.invoke(inputs, config=config)
    
    # 6. Extrakce odpovědi
    bot_reply = extract_bot_reply(result)
    
    if not bot_reply or not str(bot_reply).strip():
        bot_reply = "Ahoj! Jsem Vendy z Workia. Ráda bych si s tebou popovídala o tvé registraci."
        print("⚠️ WARNING: Graf vygeneroval prázdnou zprávu, použita fallback zpráva")
    
    print(f"💬 Odpověď Vendy: {bot_reply[:100]}...")
    
    # 7. Odeslání zprávy na Telegram
    success = await send_telegram_message(telegram_id, bot_reply)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nepodařilo se odeslat zprávu na Telegram"
        )
    
    return {
        "success": True,
        "message": "Úvodní zpráva odeslána",
        "telegram_id": telegram_id,
        "candidate_name": initial_db_data["candidate_data"].get("full_name", "")
    }


@app.get("/health")
async def health_check():
    """Healthcheck endpoint pro monitoring."""
    return {
        "status": "ok",
        "graph_ready": runtime.graph is not None,
        "pool_ready": runtime.pool is not None
    }
