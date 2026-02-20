# --- Handler pro příchozí WhatsApp zprávy ---
# Zrcadlí logiku telegram_handlers.handle_message

import asyncio
import tempfile
import runtime
from tools.sea_database import get_initial_state
from tools.voice_processor import transcribe_voice
from whatsapp_client import download_whatsapp_media, send_whatsapp_text


def _extract_bot_reply(result: dict) -> str:
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


def _normalize_phone(phone: str) -> str:
    """Normalizuje telefonní číslo – odstraní + a mezery."""
    return phone.replace("+", "").replace(" ", "").strip()


async def handle_whatsapp_message(phone_number: str, text: str) -> None:
    """
    Zpracuje příchozí WhatsApp zprávu: načte stav, spustí graf, odešle odpověď.
    phone_number: číslo v libovolném formátu (420123456789 nebo +420 123 456 789)
    """
    thread_id = _normalize_phone(phone_number)
    config = {"configurable": {"thread_id": thread_id}}

    # Kontrola stavu v paměti (checkpoint v Postgresu)
    current = runtime.graph.get_state(config)

    if current.values is None or not current.values:
        print(f"🔍 Inicializace: Tahám data ze SeaTable pro WhatsApp ID {thread_id}...")
        initial_db_data = get_initial_state(thread_id, channel="whatsapp")

        if initial_db_data:
            inputs = {
                "messages": [("user", text)],
                "row_id": initial_db_data["row_id"],
                "status": initial_db_data["status"],
                "candidate_data": initial_db_data["candidate_data"],
                "corrected_info": initial_db_data["corrected_info"],
            }
        else:
            # Kandidát nenalezen – můžeme poslat informační zprávu nebo ignorovat
            print(f"⚠️ WhatsApp: Kandidát s číslem {thread_id} nenalezen v SeaTable")
            await send_whatsapp_text(thread_id, "Nemohu tě najít v databázi.")
            return
    else:
        inputs = {"messages": [("user", text)]}

    # Spuštění grafu (blokující) – běží v executoru, aby neblokoval event loop
    result = await asyncio.to_thread(
        runtime.graph.invoke,
        inputs,
        config=config,
    )

    bot_reply = _extract_bot_reply(result)

    if not bot_reply or not str(bot_reply).strip():
        bot_reply = "Omlouvám se, ale zrovna mi to v té mé digitální hlavě trochu drhne. Zkusíš to znovu?"
        print("❌ ERROR: Bot vygeneroval prázdnou zprávu!")

    await send_whatsapp_text(thread_id, bot_reply)


async def handle_whatsapp_voice_message(phone_number: str, media_id: str) -> None:
    """
    Zpracuje hlasovou zprávu: stáhne audio, přepíše pomocí Whisperu,
    předá text do handle_whatsapp_message.
    """
    try:
        audio_bytes = await download_whatsapp_media(media_id)
    except Exception as e:
        print(f"❌ Chyba při stahování WhatsApp audia: {e}")
        await send_whatsapp_text(
            _normalize_phone(phone_number),
            "Nepodařilo se mi stáhnout hlasovou zprávu. Zkus to prosím znovu, nebo napiš textem.",
        )
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    transcribed = await transcribe_voice(tmp_path)
    # voice_processor v finally bloku maže soubor po přepisu

    if transcribed and transcribed.strip():
        await handle_whatsapp_message(phone_number, transcribed.strip())
    else:
        await send_whatsapp_text(
            _normalize_phone(phone_number),
            "Nepodařilo se mi přepis rozpoznat. Zkus to prosím znovu, nebo napiš textem.",
        )
