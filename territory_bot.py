# territory_bot.py
# Telegram-бот для інтернет-магазину Territory Comfort

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import threading

# ========== КОНФІГУРАЦІЯ ==========
TELEGRAM_TOKEN = "8620493037:AAEhpB19nqTnqLe68ndlV9TPTnEgBq1FZQc"
ADMIN_CHAT_ID = 506201498
SITE_URL = "https://rozd32-eng.github.io/territory-comfort/"
PRODUCTS_URL = "https://raw.githubusercontent.com/rozd32-eng/territory-comfort/main/erc_products.json"

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask додаток для webhook
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========
def load_products():
    """Завантажити товари з GitHub"""
    try:
        response = requests.get(PRODUCTS_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Помилка завантаження: {e}")
    return []

def get_product_by_code(code):
    """Пошук товару за кодом"""
    products = load_products()
    for product in products:
        if product.get("code") == code:
            return product
    return None

# ========== КОМАНДИ ТЕЛЕГРАМ БОТА ==========
async def start(update, context):
    """Команда /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"🏪 *Вітаємо в Territory Comfort, {user.first_name}!*\n\n"
        f"🛒 Інтернет-магазин інструментів та техніки\n"
        f"📦 Понад 26 000 товарів у наявності\n\n"
        f"🔗 Сайт: {SITE_URL}\n\n"
        f"📋 *Доступні команди:*\n"
        f"/catalog - 🛒 Каталог товарів\n"
        f"/search [назва] - 🔍 Пошук товарів\n"
        f"/product [код] - 📦 Інформація про товар\n"
        f"/contact - 📞 Контакти магазину\n\n"
        f"💬 *Швидке замовлення:* надішліть код товару",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def catalog(update, context):
    """Команда /catalog"""
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Відкрити каталог", url=f"{SITE_URL}catalog.html")
    ]])
    await update.message.reply_text(
        "📦 *Каталог Territory Comfort*\n\n"
        "Понад 26 000 інструментів, будівельної та садової техніки.\n\n"
        "🔍 *Порада:* використовуйте /search для швидкого пошуку",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def search_command(update, context):
    """Команда /search"""
    if not context.args:
        await update.message.reply_text(
            "❌ *Вкажіть назву для пошуку*\n\n"
            "Приклад: `/search ніж Stanley`\n"
            "Приклад: `/search дриль`",
            parse_mode="Markdown"
        )
        return
    
    query = " ".join(context.args).lower()
    await update.message.reply_text(f"🔍 *Шукаю:* {query}...", parse_mode="Markdown")
    
    products = load_products()
    results = []
    for p in products:
        if query in p.get("name", "").lower() or query in p.get("code", "").lower():
            results.append(p)
            if len(results) >= 5:
                break
    
    if not results:
        await update.message.reply_text(
            f"❌ *Нічого не знайдено*\n\n"
            f"Спробуйте інший запит або перегляньте каталог: {SITE_URL}catalog.html",
            parse_mode="Markdown"
        )
        return
    
    response = f"🔍 *Знайдено {len(results)} товарів:*\n\n"
    for p in results:
        response += f"🔹 *{p.get('name', 'Без назви')}*\n"
        response += f"   📋 Код: `{p.get('code', '-')}`\n"
        response += f"   💰 Ціна: {p.get('price', 0)} ₴\n"
        response += f"   📦 Наявність: {p.get('stock', 0)} шт\n"
        response += f"   🔗 /product {p.get('code', '')}\n\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def product_command(update, context):
    """Команда /product - інформація про товар"""
    if not context.args:
        await update.message.reply_text(
            "❌ *Вкажіть код товару*\n\n"
            "Приклад: `/product 0-10-088`\n\n"
            "Код можна знайти в каталозі або на сайті",
            parse_mode="Markdown"
        )
        return
    
    code = context.args[0]
    product = get_product_by_code(code)
    
    if not product:
        await update.message.reply_text(
            f"❌ *Товар з кодом `{code}` не знайдено*\n\n"
            f"Перевірте код або скористайтесь /search",
            parse_mode="Markdown"
        )
        return
    
    price = product.get('price', 0)
    old_price = product.get('old_price')
    price_text = f"{price} ₴"
    if old_price and old_price > price:
        price_text = f"~~{old_price} ₴~~ → {price} ₴"
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Замовити", callback_data=f"order_{code}"),
        InlineKeyboardButton("📱 Відкрити на сайті", url=f"{SITE_URL}product.html?code={code}")
    ]])
    
    response = f"""🔧 *{product.get('name', 'Товар')}*

📋 *Код:* `{code}`
💰 *Ціна:* {price_text}
📦 *Наявність:* {product.get('stock', 0)} шт
🏢 *Виробник:* {product.get('vendor', 'Невідомо')}

🔗 *Посилання:* {SITE_URL}product.html?code={code}"""
    
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=keyboard)

async def contact_command(update, context):
    """Команда /contact"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Зателефонувати", url="tel:+380441234567")],
        [InlineKeyboardButton("💬 Написати в Telegram", url="https://t.me/TerritorySupport")],
        [InlineKeyboardButton("📧 Написати Email", url="mailto:info@territorycomfort.ua")]
    ])
    
    await update.message.reply_text(
        "📞 *Контакти Territory Comfort*\n\n"
        "🏢 *Адреса:* м. Київ, вул. Інструментальна, 15\n"
        "📱 *Телефон:* +380 (44) 123-45-67\n"
        "📧 *Email:* info@territorycomfort.ua\n"
        "⏰ *Графік:* Пн-Пт 9:00-18:00\n\n"
        "🌐 *Сайт:* " + SITE_URL + "\n"
        "📸 *Instagram:* @territory_comfort\n"
        "💬 *Підтримка:* @TerritorySupport",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def handle_callback(update, context):
    """Обробка натискань кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("order_"):
        code = query.data[6:]
        product = get_product_by_code(code)
        if product:
            await query.edit_message_text(
                f"✅ *Товар додано до кошика!*\n\n"
                f"🔧 {product.get('name')}\n"
                f"💰 {product.get('price', 0)} ₴\n\n"
                f"Для оформлення замовлення перейдіть на сайт:\n"
                f"{SITE_URL}cart.html",
                parse_mode="Markdown"
            )

# ========== WEBHOOK ДЛЯ ЗАМОВЛЕНЬ ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    """Отримання замовлень з сайту"""
    try:
        order_data = request.json
        logger.info(f"Нове замовлення: {order_data.get('number')}")
        
        # Формуємо повідомлення
        items_text = ""
        for item in order_data.get('items', []):
            items_text += f"• {item.get('name')} x{item.get('quantity')} = {item.get('price') * item.get('quantity')} ₴\n"
        
        message = f"""🛒 *НОВЕ ЗАМОВЛЕННЯ!*

№: {order_data.get('number')}
👤 Клієнт: {order_data.get('customer_name', 'Невідомо')}
📞 Телефон: {order_data.get('customer_phone', '-')}
📧 Email: {order_data.get('customer_email', '-')}

📦 *Товари:*
{items_text}
💰 *Загалом:* {order_data.get('total', 0)} ₴

🔗 Посилання: /order_{order_data.get('number')}"""
        
        # Надсилаємо адміну
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=message, parse_mode="Markdown")
        
        # Підтвердження клієнту
        if order_data.get('telegram_user_id'):
            bot.send_message(
                chat_id=order_data['telegram_user_id'],
                text=f"✅ *Дякуємо за замовлення №{order_data.get('number')}!*\n\n"
                     f"Сума: {order_data.get('total', 0)} ₴\n"
                     f"Статус: 🆕 Прийнято в обробку\n\n"
                     f"Ми зв'яжемося з вами найближчим часом.\n"
                     f"🔗 {SITE_URL}",
                parse_mode="Markdown"
            )
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Помилка webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Перевірка стану бота"""
    return jsonify({"status": "ok", "bot": "Territory Comfort"}), 200

# ========== ЗАПУСК БОТА ==========
def setup_bot():
    """Налаштування команд"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("catalog", catalog))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("product", product_command))
    application.add_handler(CommandHandler("contact", contact_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    return application

if __name__ == "__main__":
    # Запускаємо Flask в окремому потоці
    def run_flask():
        app.run(host="0.0.0.0", port=8080)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Запускаємо бота
    bot_app = setup_bot()
    print("🤖 Бот Territory Comfort запущений!")
    print(f"🔗 Webhook: http://localhost:8080/webhook")
    bot_app.run_polling(allowed_updates=["message", "callback_query"])
