#!/usr/bin/env python3
"""
Wizard of Oz режим (ТЗ раздел 2.4) — первые 50 запросов.

Запуск:
    python test_run.py "робот-пылесос до 30к для кота с длинной шерстью"

Скрипт запускает AI-пайплайн локально и выводит результат в консоль.
Для отправки результата пользователю скопируй JSON и отправь через бота.
"""
import asyncio
import json
import sys
import os

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")


async def main(query: str) -> None:
    from app.ai.pipeline import run_search_pipeline

    print(f"\n{'='*60}")
    print(f"Запрос: {query}")
    print("="*60)
    print("Запускаю пайплайн...\n")

    # Заглушка объекта юзера
    class FakeUser:
        id = 0
        quiz_data = {}
        is_premium = True

    result = await run_search_pipeline(query, FakeUser())

    if result.get("needs_clarification"):
        print(f"❓ НУЖНО УТОЧНЕНИЕ: {result.get('clarification')}\n")
        return

    products = result.get("products", [])
    print(f"✅ Найдено {len(products)} варианта\n")

    for p in products:
        medal = ["🥇", "🥈", "🥉"][p["rank"] - 1]
        print(f"{medal} {p['name']}")
        print(f"   Причина: {p['reason']}")
        for price in p.get("prices", []):
            star = "★" if price.get("is_best") else " "
            print(f"  {star} {price['marketplace']}: {price['price']:,} ₽")
        print()

    print(f"📤 Текст для шеринга:")
    print(result.get("share_text", ""))
    print()

    output_file = "test_run_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"💾 Полный результат сохранён в {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python test_run.py <запрос>")
        print("Пример: python test_run.py \"наушники с ANC до 15к\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    asyncio.run(main(query))
