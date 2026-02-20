# --- Webhook Server pro proaktivní spuštění Vendy ---
# FastAPI endpoint pro WhatsApp webhook a zahájení konverzace

import hashlib
import hmac
import asyncio
import os
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import runtime
from tools.sea_database import get_initial_state
from whatsapp_handlers import handle_whatsapp_message, handle_whatsapp_voice_message
from whatsapp_client import send_whatsapp_template

load_dotenv()

app = FastAPI(title="Vendy Webhook Server")


class WebhookStartWhatsAppRequest(BaseModel):
    whatsapp_phone: str


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

    template_name = os.getenv("WHATSAPP_TEMPLATE_NAME", "workia_hello")
    template_lang = os.getenv("WHATSAPP_TEMPLATE_LANG", "en")
    full_name = initial_db_data["candidate_data"].get("full_name", "")
    first_name = full_name.split()[0] if full_name else ""

    components = [
        {"type": "header", "parameters": [{"type": "text", "text": "workia"}]},
        {"type": "body", "parameters": [{"type": "text", "text": first_name or "there"}]},
    ]

    success = await send_whatsapp_template(
        to=whatsapp_phone,
        template_name=template_name,
        lang=template_lang,
        components=components,
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


def _extract_message_text(msg: dict) -> str:
    """
    Extrahuje text z příchozí WhatsApp zprávy.
    Podporuje: text, button (odpověď na tlačítko v šabloně), interactive (button_reply).
    """
    msg_type = msg.get("type", "")
    if msg_type == "text":
        return msg.get("text", {}).get("body", "").strip()
    if msg_type == "button":
        # Odpověď na quick-reply tlačítko v šabloně
        btn = msg.get("button", {})
        return (btn.get("text") or btn.get("payload") or "").strip()
    if msg_type == "interactive":
        # Odpověď na tlačítko v interaktivní zprávě
        interactive = msg.get("interactive", {})
        if interactive.get("type") == "button_reply":
            br = interactive.get("button_reply", {})
            return (br.get("title") or br.get("id") or "").strip()
        if interactive.get("type") == "list_reply":
            lr = interactive.get("list_reply", {})
            return (lr.get("title") or lr.get("id") or "").strip()
    return ""


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
                from_id = msg.get("from", "")
                msg_type = msg.get("type", "")

                if msg_type == "audio":
                    media_id = msg.get("audio", {}).get("id")
                    if media_id:
                        asyncio.create_task(
                            handle_whatsapp_voice_message(from_id, media_id)
                        )
                else:
                    text_body = _extract_message_text(msg)
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
