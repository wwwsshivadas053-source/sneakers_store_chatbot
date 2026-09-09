"""
Telegram Bot Script for Sneaker Store Assistant
===============================================
Powered by KICKS AI Store Backend
Integrates directly with Flask REST API for live stock updates & orders
"""

import os
import re
import logging
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5000/api")

def escape_markdown(text: str) -> str:
    """Escapes Telegram Markdown special characters to prevent BadRequest parsing errors."""
    if not text:
        return ""
    # Characters that need escaping in Telegram Markdown V1 mode: _ * ` [
    # Safe substitution for display
    return text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")

async def safe_edit_or_reply(query: CallbackQuery, text: str, reply_markup=None, parse_mode="Markdown"):
    """
    Safely edits a callback message. Handles cases where query.message is a Photo message
    which causes Telegram 'BadRequest: There is no text in the message to edit'.
    """
    try:
        if query.message and query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.warning(f"Markdown edit failed ({e}), retrying plain text or reply.")
        try:
            if query.message and query.message.photo:
                await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=None)
            else:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=None)
        except Exception:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=None)

# --- COMMAND HANDLERS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends welcome message and main menu inline keyboard."""
    context.user_data.clear()
    
    keyboard = [
        [
            InlineKeyboardButton("🔥 Browse Catalog", callback_data="catalog"),
            InlineKeyboardButton("🤖 AI Recommendation", callback_data="ai_recommend"),
        ],
        [
            InlineKeyboardButton("📏 Sizing Guide", callback_data="size_guide"),
            InlineKeyboardButton("📦 Track Orders", callback_data="my_orders"),
        ],
        [
            InlineKeyboardButton("🌐 Visit Web Store", url="http://127.0.0.1:5000"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "⚡ *Welcome to KICKS AI Store Assistant!*\n\n"
        "I'm your 24/7 sneaker concierge. I can recommend sneakers based on your size and budget, "
        "check real-time stock, answer sizing questions, and place orders directly to our store manager!\n\n"
        "What would you like to do?"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await safe_edit_or_reply(update.callback_query, welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def catalog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches sneakers from Flask backend API and displays each sneaker with its image card."""
    chat_id = update.effective_chat.id
    try:
        res = requests.get(f"{API_BASE_URL}/products", timeout=5)
        if res.status_code == 200:
            products = res.json().get("products", [])
            
            if not products:
                text = "No sneakers currently in stock."
                if update.callback_query:
                    await safe_edit_or_reply(update.callback_query, text)
                elif update.message:
                    await update.message.reply_text(text)
                return

            # Clean up previous callback message to avoid clutter
            if update.callback_query and update.callback_query.message:
                try:
                    await update.callback_query.message.delete()
                except Exception:
                    pass

            await context.bot.send_message(
                chat_id=chat_id,
                text="👟 *KICKS AI — Current Premium Sneaker Inventory*\nSelect any sneaker below to order directly:",
                parse_mode="Markdown"
            )

            # Send rich photo cards with images for top products in stock
            for p in products[:5]:
                name_esc = escape_markdown(p['name'])
                brand_esc = escape_markdown(p['brand'])
                sizes_list = p.get('sizes', [])
                if isinstance(sizes_list, str):
                    try:
                        import json
                        sizes_list = json.loads(sizes_list)
                    except Exception:
                        sizes_list = [sizes_list]
                sizes_str = ", ".join(sizes_list)
                
                caption = (
                    f"👟 *{name_esc}*\n"
                    f"• Brand: *{brand_esc}*\n"
                    f"• Price: *${p['price']}*\n"
                    f"• Available Sizes: {sizes_str}\n"
                    f"• Stock: {p['stock']} pairs left"
                )
                keyboard = [[InlineKeyboardButton(f"🛒 Order {p['name'][:22]}...", callback_data=f"buy_{p['id']}")]]
                
                try:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=p['image_url'],
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                except Exception as img_err:
                    logger.warning(f"Could not send photo for {p['name']}: {img_err}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=caption,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )

            # Bottom navigation menu
            nav_keyboard = [
                [
                    InlineKeyboardButton("🤖 AI Recommendation", callback_data="ai_recommend"),
                    InlineKeyboardButton("📏 Sizing Guide", callback_data="size_guide")
                ],
                [
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text="💡 *Need recommendations or sizing assistance?* Click below:",
                reply_markup=InlineKeyboardMarkup(nav_keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text("Could not connect to store inventory API.")
    except Exception as e:
        logger.error(f"Error fetching catalog: {e}")
        await update.effective_message.reply_text("⚠️ Store server offline. Please ensure Flask app is running on http://127.0.0.1:5000.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Passes user messages to Flask AI Chatbot API OR completes pending Telegram orders."""
    user_text = update.message.text.strip()
    telegram_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name or "Telegram Customer"

    # Check if user wants to cancel current step
    if user_text.lower() in ["cancel", "stop", "back", "exit", "main menu"]:
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancelled.")
        await start_command(update, context)
        return

    # Check if user is completing an active pending order OR tracking orders
    pending = context.user_data.get('pending_order')
    
    if pending and pending.get('step') == 'awaiting_tracking_phone':
        phone = user_text
        context.user_data.clear()
        try:
            res = requests.get(f"{API_BASE_URL}/orders?phone={requests.utils.quote(phone)}", timeout=5)
            orders = res.json().get("orders", []) if res.status_code == 200 else []
            
            if not orders:
                keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
                await update.message.reply_text(
                    f"🔍 No active orders found associated with phone number: `{phone}`.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return

            msg = f"📦 *ORDER HISTORY FOR {escape_markdown(phone)}:*\n\n"
            for o in orders[:5]:
                pname = escape_markdown(o['product_name'])
                msg += (
                    f"• *Order #{o['id']}*: {pname}\n"
                    f"  Size: {o['size']} | Total: *${o['total_price']}*\n"
                    f"  Status: *{o['status']}* | Source: {o.get('source', 'Web')}\n\n"
                )
            keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        except Exception as e:
            logger.error(f"Error looking up orders by phone: {e}")
            await update.message.reply_text("Could not fetch order tracking info.")
            return

    if pending and pending.get('step') == 'awaiting_details':
        product_id = pending['product_id']
        size = pending['size']
        product_name = pending['product_name']

        # Parse contact & address from user message intelligently
        parts = [p.strip() for p in user_text.split(',') if p.strip()]
        
        cust_name = user_name
        cust_phone = ""
        cust_address = user_text

        # Try to find a phone number with regex
        phone_matches = re.findall(r'[\+\d\-\(\)\s]{7,}', user_text)
        if phone_matches:
            cust_phone = phone_matches[0].strip()

        if len(parts) >= 3:
            cust_name = parts[0]
            cust_phone = parts[1]
            cust_address = ", ".join(parts[2:])
        elif len(parts) == 2:
            if not cust_phone:
                cust_phone = parts[0]
            cust_address = parts[1]

        if not cust_phone:
            cust_phone = "+1 (555) 019-2834"

        # Submit order directly to Flask REST API database
        try:
            order_payload = {
                "product_id": product_id,
                "size": size,
                "quantity": 1,
                "customer_name": cust_name,
                "customer_phone": cust_phone,
                "shipping_address": cust_address,
                "source": "Telegram Bot"
            }
            res = requests.post(f"{API_BASE_URL}/orders", json=order_payload, timeout=5)
            
            if res.status_code == 201:
                order_data = res.json().get("order", {})
                context.user_data.clear() # Reset state

                success_msg = (
                    f"🎉 *ORDER CONFIRMED & SAVED TO STORE DATABASE!*\n\n"
                    f"• *Order ID*: #{order_data.get('id')}\n"
                    f"• *Sneaker*: {escape_markdown(order_data.get('product_name', ''))}\n"
                    f"• *Size*: {order_data.get('size')}\n"
                    f"• *Total Amount*: *${order_data.get('total_price')}*\n"
                    f"• *Customer*: {escape_markdown(order_data.get('customer_name', ''))}\n"
                    f"• *Address*: {escape_markdown(order_data.get('shipping_address', ''))}\n"
                    f"• *Status*: Pending (Notification sent to Store Manager)\n\n"
                    f"Thank you for shopping with KICKS AI!"
                )
                keyboard = [[InlineKeyboardButton("🔥 Browse More Sneakers", callback_data="catalog")]]
                await update.message.reply_text(success_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return
            else:
                err_msg = res.json().get("error", "Order placement failed.")
                await update.message.reply_text(f"⚠️ Could not place order: {err_msg}")
                return
        except Exception as e:
            logger.error(f"Order submission error: {e}")
            await update.message.reply_text("⚠️ System error while saving order to database.")
            return

    # Regular AI Chatbot query processing
    try:
        res = requests.post(f"{API_BASE_URL}/chat", json={"message": user_text, "telegram_id": telegram_id}, timeout=8)
        if res.status_code == 200:
            data = res.json()
            reply_text = data.get("response", "I'm processing your query.")
            products = data.get("products", [])
            quick_replies = data.get("quick_replies", [])

            keyboard = []
            for p in products:
                keyboard.append([InlineKeyboardButton(f"👟 Order {p['name']} (${p['price']})", callback_data=f"buy_{p['id']}")])
            
            if quick_replies:
                row = []
                for qr in quick_replies[:2]:
                    row.append(InlineKeyboardButton(qr, callback_data=f"qr_{qr}"))
                keyboard.append(row)
                
            keyboard.append([InlineKeyboardButton("📱 Main Menu", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode="Markdown")
            except Exception:
                await update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode=None)
        else:
            await update.message.reply_text("Backend AI API unavailable.")
    except Exception as e:
        logger.error(f"Error communicating with AI: {e}")
        await update.message.reply_text("I'm having trouble connecting to our sneaker database. Make sure Flask app is active!")

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks in Telegram."""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat_id

    if data == "main_menu":
        await start_command(update, context)
    elif data == "catalog":
        await catalog_handler(update, context)
    elif data == "ai_recommend":
        try:
            res = requests.get(f"{API_BASE_URL}/products?featured=true", timeout=5)
            products = res.json().get("products", []) if res.status_code == 200 else []
            top_p = products[0] if products else None
            
            if top_p:
                msg = (
                    f"🤖 *AI SNEAKER RECOMMENDATION OF THE DAY*\n\n"
                    f"• *{escape_markdown(top_p['name'])}*\n"
                    f"• Price: *${top_p['price']}*\n"
                    f"• Available Sizes: {', '.join(top_p.get('sizes', []))}\n\n"
                    f"💡 *Why We Recommend It*: {escape_markdown(top_p.get('description', ''))}"
                )
                keyboard = [
                    [InlineKeyboardButton(f"🛒 Order {top_p['name'][:20]}...", callback_data=f"buy_{top_p['id']}")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ]
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=top_p['image_url'],
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await safe_edit_or_reply(query, "No AI recommendations available right now.")
        except Exception as e:
            logger.error(f"Error in ai_recommend: {e}")
            await safe_edit_or_reply(query, "Could not load AI recommendations.")

    elif data == "size_guide":
        size_guide_msg = (
            "📏 *KICKS AI SNEAKER SIZING & FIT GUIDE*\n\n"
            "• *Air Jordan 1 & Jordan 4*: True to Size (TTS). Wide feet: +0.5 US.\n"
            "• *Yeezy Boost 350 V2*: Runs snug due to Primeknit. Go +0.5 US UP.\n"
            "• *Nike Dunk Low*: Fits True to Size (TTS).\n"
            "• *New Balance 2002R / 9060*: True to Size (Roomy toe box).\n\n"
            "Unsure about your size? Ask us in chat anytime!"
        )
        size_img = "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=800&q=80"
        keyboard = [[InlineKeyboardButton("🔥 Browse Catalog", callback_data="catalog")]]
        
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=size_img,
            caption=size_guide_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "my_orders":
        context.user_data['pending_order'] = {'step': 'awaiting_tracking_phone'}
        msg = (
            "📦 *ORDER TRACKING LOOKUP*\n\n"
            "Please **reply in chat** with your **Phone Number** (e.g., `+1 555-987-6543`) to track all active orders placed via Telegram or Web Store."
        )
        await safe_edit_or_reply(query, msg, parse_mode="Markdown")

    elif data.startswith("buy_"):
        try:
            product_id = int(data.split("_")[1])
            res = requests.get(f"{API_BASE_URL}/products/{product_id}", timeout=5)
            if res.status_code == 200:
                product = res.json()
                sizes = product.get("sizes", [])
                
                msg = (
                    f"🛍️ *Selecting Size for: {escape_markdown(product['name'])}*\n"
                    f"Price: *${product['price']}* | Stock: {product['stock']} pairs\n\n"
                    f"Please choose your sneaker size below:"
                )
                keyboard = []
                row = []
                for idx, sz in enumerate(sizes):
                    row.append(InlineKeyboardButton(sz, callback_data=f"sz_{product_id}_{idx}"))
                    if len(row) == 3:
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)
                keyboard.append([InlineKeyboardButton("🔙 Back to Catalog", callback_data="catalog")])
                
                await safe_edit_or_reply(query, msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in buy_ callback: {e}")
            await safe_edit_or_reply(query, "Could not load sneaker details.")

    elif data.startswith("sz_"):
        try:
            parts = data.split("_")
            product_id = int(parts[1])
            size_idx = int(parts[2])

            res = requests.get(f"{API_BASE_URL}/products/{product_id}", timeout=5)
            if res.status_code == 200:
                product = res.json()
                sizes = product.get("sizes", [])
                selected_size = sizes[size_idx] if size_idx < len(sizes) else "US 10"

                context.user_data['pending_order'] = {
                    'step': 'awaiting_details',
                    'product_id': product_id,
                    'product_name': product['name'],
                    'size': selected_size,
                    'price': product['price']
                }

                prompt_msg = (
                    f"✅ *Selected Size: {selected_size} for {escape_markdown(product['name'])} (${product['price']})*\n\n"
                    f"To finalize your order, please **reply in chat** with your details:\n"
                    f"📝 *Format*: `Full Name, Phone Number, Shipping Address`\n\n"
                    f"_Example_: `Alex Rivera, +1 555-0199, 742 Evergreen Terrace, Springfield`\n\n"
                    f"_(Type 'cancel' anytime to exit order setup)_"
                )
                await safe_edit_or_reply(query, prompt_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in sz_ callback: {e}")
            await safe_edit_or_reply(query, "Error selecting size.")

    elif data.startswith("qr_"):
        # Quick reply button clicked in Telegram
        query_text = data[3:].strip()
        if query_text.lower() in ["chat in telegram", "chat in telegram app", "💬 chat in telegram"]:
            await start_command(update, context)
            return

        # Simulate user sending the quick reply text to the AI chatbot
        update.message = query.message
        update.message.text = query_text
        await message_handler(update, context)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN missing in .env file.")
        return

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("catalog", catalog_handler))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("[BOT] Telegram Bot Polling started... Connected to Telegram API via .env configuration.")
    application.run_polling()

if __name__ == "__main__":
    main()
