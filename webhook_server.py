# --- Webhook Server pro proaktivní spuštění Vendy ---
# FastAPI endpoint, který přijme telegram_id a zahájí konverzaci

import hashlib
import hmac
import asyncio
import os
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

import runtime
from tools.sea_database import get_initial_state
from whatsapp_handlers import handle_whatsapp_message
from whatsapp_client import send_whatsapp_template

load_dotenv()

app = FastAPI(title="Vendy Webhook Server")

# Pydantic modely pro request body
class WebhookStartRequest(BaseModel):
    telegram_id: str


class WebhookStartWhatsAppRequest(BaseModel):
    whatsapp_phone: str


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


@app.post("/webhook/start/whatsapp")
async def webhook_start_whatsapp(request: WebhookStartWhatsAppRequest):
    """
    Webhook pro zahájení konverzace přes WhatsApp.
    Odešle schválenou šablonu – první kontakt musí být šablona (24h okno).
    """
    whatsapp_phone = request.whatsapp_phone.replace("+", "").replace(" ", "").strip()
    print(f"🔔 Webhook přijat pro whatsapp_phone: {whatsapp_phone}")

    initial_db_data = get_initial_state(whatsapp_phone, channel="whatsapp")

    if not initial_db_data:
        raise HTTPException(
            status_code=404,
            detail=f"Kandidát s whatsapp_phone {whatsapp_phone} nebyl nalezen v SeaTable"
        )

    template_name = os.getenv("WHATSAPP_TEMPLATE_NAME", "hello_world")
    template_lang = os.getenv("WHATSAPP_TEMPLATE_LANG", "cs")

    success = await send_whatsapp_template(
        to=whatsapp_phone,
        template_name=template_name,
        lang=template_lang,
        components=None,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nepodařilo se odeslat šablonu na WhatsApp"
        )

    return {
        "success": True,
        "message": "Úvodní šablona odeslána",
        "whatsapp_phone": whatsapp_phone,
        "candidate_name": initial_db_data["candidate_data"].get("full_name", ""),
    }


def _verify_whatsapp_signature(body: bytes, signature: str) -> bool:
    """Ověří X-Hub-Signature-256 pomocí WHATSAPP_APP_SECRET."""
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    if not app_secret:
        print("⚠️ WHATSAPP_APP_SECRET není nastaven – přeskočena validace podpisu")
        return True
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@app.get("/webhook/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """
    GET endpoint pro ověření webhooku při nastavování v Meta Developer Console.
    Pokud hub.verify_token odpovídá WHATSAPP_VERIFY_TOKEN, vrátí hub.challenge.
    """
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    if hub_mode == "subscribe" and verify_token and hub_verify_token == verify_token:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verifikace selhala")


@app.post("/webhook/whatsapp")
async def whatsapp_webhook_post(request: Request):
    """
    POST endpoint pro příchozí WhatsApp zprávy.
    Meta vyžaduje rychlou odpověď 200 – zpracování probíhá na pozadí.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not _verify_whatsapp_signature(body, signature):
        raise HTTPException(status_code=401, detail="Neplatný podpis")

    if runtime.graph is None:
        raise HTTPException(status_code=503, detail="Graf není inicializován")

    data = await request.json()

    if data.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                if msg.get("type") != "text":
                    continue
                from_id = msg.get("from", "")
                text_obj = msg.get("text", {})
                text_body = text_obj.get("body", "")

                if text_body:
                    asyncio.create_task(
                        handle_whatsapp_message(from_id, text_body)
                    )

    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """Healthcheck endpoint pro monitoring."""
    return {
        "status": "ok",
        "graph_ready": runtime.graph is not None,
        "pool_ready": runtime.pool is not None
    }
