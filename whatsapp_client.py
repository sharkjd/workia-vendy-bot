# --- WhatsApp Cloud API klient ---
# Odesílání textových zpráv a šablon přes Meta Graph API

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _get_phone_number_id() -> str:
    """Vrátí ID telefonního čísla z env."""
    pid = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not pid:
        raise ValueError("WHATSAPP_PHONE_NUMBER_ID není nastaven v .env")
    return pid


def _get_access_token() -> str:
    """Vrátí access token z env."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not token:
        raise ValueError("WHATSAPP_ACCESS_TOKEN není nastaven v .env")
    return token


def _normalize_phone(to: str) -> str:
    """Normalizuje telefonní číslo – odstraní + a mezery."""
    return to.replace("+", "").replace(" ", "").strip()


async def download_whatsapp_media(media_id: str) -> bytes:
    """
    Stáhne mediální soubor z WhatsApp Cloud API (audio, obrázek, atd.).
    Dvoustupňový proces: 1) získat URL, 2) stáhnout binární data.
    Vrací bytes nebo vyhodí výjimku při chybě.
    """
    headers = {"Authorization": f"Bearer {_get_access_token()}"}
    phone_id = _get_phone_number_id()
    url = f"{BASE_URL}/{media_id}?phone_number_id={phone_id}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        media_url = data.get("url")
        if not media_url:
            raise ValueError("WhatsApp API nevrátila URL pro media")

        download_resp = await client.get(media_url, headers=headers)
        download_resp.raise_for_status()
        return download_resp.content


async def send_whatsapp_text(to: str, body: str) -> bool:
    """
    Odešle běžnou textovou zprávu (odpověď v rámci 24h okna).
    Vrací True pokud se podařilo, jinak False.
    """
    phone = _normalize_phone(to)
    url = f"{BASE_URL}/{_get_phone_number_id()}/messages"
    headers = {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": body,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"✅ Zpráva odeslána na WhatsApp (to: {phone})")
            return True
        else:
            print(f"❌ Chyba při odesílání na WhatsApp: {response.text}")
            return False


async def send_whatsapp_template(
    to: str,
    template_name: str,
    lang: str = "cs",
    components: list | None = None,
) -> bool:
    """
    Odešle šablonovou zprávu (pro první kontakt mimo 24h okno).
    components: seznam komponent šablony (body, header, buttons...)
    např. [{"type": "body", "parameters": [{"type": "text", "text": "Jan"}]}]
    Vrací True pokud se podařilo, jinak False.
    """
    phone = _normalize_phone(to)
    url = f"{BASE_URL}/{_get_phone_number_id()}/messages"
    headers = {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
    }

    template_payload: dict = {
        "name": template_name,
        "language": {"code": lang},
    }
    if components:
        template_payload["components"] = components

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "template",
        "template": template_payload,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"✅ Šablona odeslána na WhatsApp (to: {phone}, template: {template_name})")
            return True
        else:
            print(f"❌ Chyba při odesílání šablony na WhatsApp: {response.text}")
            return False
