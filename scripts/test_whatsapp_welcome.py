#!/usr/bin/env python3
"""
Jednoduchý skript pro otestování odeslání welcome zprávy přes WhatsApp.

Použití:
  python scripts/test_whatsapp_welcome.py +420123456789
  python scripts/test_whatsapp_welcome.py 420123456789 --template
  python scripts/test_whatsapp_welcome.py +420123456789 --text "Ahoj! Jsem Vendy."
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Přidání kořene projektu do path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from whatsapp_client import send_whatsapp_text, send_whatsapp_template


async def main():
    parser = argparse.ArgumentParser(description="Otestuj odeslání welcome zprávy na WhatsApp")
    parser.add_argument(
        "phone",
        help="Telefonní číslo příjemce (např. +420123456789 nebo 420123456789)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--template",
        action="store_true",
        help="Odešli šablonu (hello_world nebo WHATSAPP_TEMPLATE_NAME z .env)",
    )
    parser.add_argument(
        "--header",
        type=str,
        help="Hodnota pro proměnnou v záhlaví šablony (např. workia)",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Jméno pro proměnnou v textu šablony (např. Honzo)",
    )
    parser.add_argument(
        "--template-name",
        type=str,
        help="Název šablony (přepíše WHATSAPP_TEMPLATE_NAME z .env)",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="cs",
        help="Jazyk šablony (default: cs)",
    )
    group.add_argument(
        "--text",
        type=str,
        default="Ahoj! Jsem Vendy z Workia. Ráda bych si s tebou popovídala o tvé registraci.",
        metavar="ZPRÁVA",
        help="Odešli vlastní textovou zprávu (default: welcome text)",
    )
    args = parser.parse_args()

    phone = args.phone.replace("+", "").replace(" ", "").strip()
    if not phone.isdigit():
        print("❌ Neplatné telefonní číslo – použij jen číslice (např. 420123456789)")
        sys.exit(1)

    print(f"📱 Odesílám na: {phone}")
    print("-" * 40)

    if args.template:
        template_name = args.template_name or os.getenv("WHATSAPP_TEMPLATE_NAME", "hello_world")
        template_lang = args.lang or os.getenv("WHATSAPP_TEMPLATE_LANG", "cs")
        components = None
        if args.header is not None or args.name is not None:
            components = []
            if args.header is not None:
                components.append({
                    "type": "header",
                    "parameters": [{"type": "text", "text": args.header}],
                })
            if args.name is not None:
                components.append({
                    "type": "body",
                    "parameters": [{"type": "text", "text": args.name}],
                })
        print(f"📋 Šablona: {template_name} ({template_lang})")
        if components:
            print(f"   Header: {args.header!r}, Jméno: {args.name!r}")
        success = await send_whatsapp_template(
            to=phone,
            template_name=template_name,
            lang=template_lang,
            components=components,
        )
    else:
        print(f"💬 Text: {args.text[:60]}{'...' if len(args.text) > 60 else ''}")
        success = await send_whatsapp_text(phone, args.text)

    print("-" * 40)
    if success:
        print("✅ Hotovo! Zkontroluj WhatsApp na zadaném čísle.")
    else:
        print("❌ Odeslání selhalo. Zkontroluj .env (WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID).")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
