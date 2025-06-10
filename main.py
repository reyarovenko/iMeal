# main.py - Fixed version
import os
import logging
from typing import Dict, List
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Enable logging for diagnostics
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import multi-agent system
try:
    from multiagent_core import SimpleCoordinator

    logger.info("✅ MultiAgent system loaded successfully")
except ImportError as e:
    logger.error(f"Error importing multiagent_core: {e}")


    # Create stub
    class SimpleCoordinator:
        def __init__(self):
            self.user_languages = {}
            self.user_states = {}

        async def route_request(self, user_id, action, data):
            return {"status": "success", "message": f"Test response for action: {action}"}

load_dotenv()
logger.info(".env file loaded")

# Global coordinator
coordinator = SimpleCoordinator()


# ============================================================================
# MAIN COMMANDS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /start"""
    logger.info(f"/start command from user {update.effective_user.id}")

    keyboard = [
        [KeyboardButton("🇺🇦 Українська")],
        [KeyboardButton("🇬🇧 English")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    try:
        await update.message.reply_text("⬇️ Виберіть мову / Choose language:", reply_markup=reply_markup)
        logger.info("Response to /start sent")
    except Exception as e:
        logger.error(f"Error sending response to /start: {e}")


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set language"""
    text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Setting language: {text} for user {user_id}")

    try:
        if "Українська" in text:
            coordinator.user_languages[user_id] = "uk"
            await update.message.reply_text("✅ Мову встановлено: українська")
            await show_main_menu(update, context)
        elif "English" in text:
            coordinator.user_languages[user_id] = "en"
            await update.message.reply_text("Language set to: English")
            await show_main_menu(update, context)
        else:
            logger.warning(f"Unknown language choice: {text}")
            # FIX: don't return without response
            await update.message.reply_text("Невідомий вибір мови / Unknown language choice")

        logger.info("Language set successfully")
    except Exception as e:
        logger.error(f"Error setting language: {e}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def user_has_language(user_id: int) -> bool:
    """Check if user has selected language"""
    return user_id in coordinator.user_languages


def is_language_command(text: str) -> bool:
    """Check if text is a language selection command"""
    return text in ["🇺🇦 Українська", "🇬🇧 English"]


def is_menu_command(text: str) -> bool:
    """Check if text is a menu command"""
    menu_commands = [
        "📊 Аналітик", "📊 Analyst", "🍎 Дієтолог", "🍎 Dietitian",
        "➕ Додати їжу", "➕ Add food", "🗑️ Видалити їжу", "🗑️ Delete food",
        "📊 Підсумок дня", "📊 Daily summary", "🧮 Розрахувати калораж",
        "🧮 Calculate calories", "💡 Рекомендації", "💡 Recommendations",
        "📋 Мій профіль", "📋 My profile", "⬅️ Назад", "⬅️ Back"
    ]
    return text in menu_commands


# ============================================================================
# MENUS
# ============================================================================

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main menu"""
    user_id = update.effective_user.id
    lang = coordinator.user_languages.get(user_id, "uk")
    logger.info(f"Showing main menu for user {user_id}, language: {lang}")

    try:
        if lang == "uk":
            keyboard = [
                ["📊 Аналітик", "🍎 Дієтолог"]
            ]
            text = "📊 Аналітик - підрахунок КБЖУ\n🍎 Дієтолог - рекомендації"
        else:
            keyboard = [
                ["📊 Analyst", "🍎 Dietitian"]
            ]
            text = "Analyst - calories and macros calculation\n🍎 Dietitian - recommendations"

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup=reply_markup)
        logger.info("Main menu sent")
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")


async def show_analyst_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Analyst menu"""
    logger.info(f"Showing analyst menu, language: {lang}")

    try:
        if lang == "uk":
            keyboard = [
                ["➕ Додати їжу", "🗑️ Видалити їжу"],
                ["📊 Підсумок дня"],
                ["⬅️ Назад"]
            ]
            text = "Оберіть дію з меню"
        else:
            keyboard = [
                ["➕ Add food", "🗑️ Delete food"],
                ["📊 Daily summary"],
                ["⬅️ Back"]
            ]
            text = "Choose menu action"

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup=reply_markup)
        logger.info("Analyst menu sent")
    except Exception as e:
        logger.error(f"Error showing analyst menu: {e}")


async def show_dietitian_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Dietitian menu"""
    logger.info(f"Showing dietitian menu, language: {lang}")

    try:
        if lang == "uk":
            keyboard = [
                ["🧮 Розрахувати калораж", "💡 Рекомендації"],
                ["📋 Мій профіль", "⬅️ Назад"]
            ]
            text = "🍎 Дієтолог"
        else:
            keyboard = [
                ["🧮 Calculate calories", "💡 Recommendations"],
                ["📋 My profile", "⬅️ Back"]
            ]
            text = "🍎 Dietitian"

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup=reply_markup)
        logger.info("Dietitian menu sent")
    except Exception as e:
        logger.error(f"Error showing dietitian menu: {e}")


# ============================================================================
# RESULT SENDER
# ============================================================================

async def send_result(update: Update, result: Dict, lang: str):
    """Send result to user"""
    logger.info(f"Sending result: {result}")

    try:
        status = result.get("status")

        if status == "success":
            logger.info("Operation completed successfully!")
        elif status == "error":
            logger.error(f"Error: 'Unknown error'")
        else:
            logger.info("ℹResult received")

        await update.message.reply_text(message)
        logger.info("Result sent")
    except Exception as e:
        logger.error(f"Error sending result: {e}")


# ============================================================================
# MAIN MESSAGE HANDLER - FIXED VERSION
# ============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main message handler - FIXED VERSION"""
    user_id = update.effective_user.id
    text = update.message.text
    logger.info(f"Message received from {user_id}: '{text}'")

    try:
        # FIX 1: Proper language check
        if not user_has_language(user_id):
            logger.info(f"User {user_id} hasn't selected language")

            if is_language_command(text):
                # Process language selection
                await set_language(update, context)
            else:
                # Show language selection
                keyboard = [
                    [KeyboardButton("🇺🇦 Українська")],
                    [KeyboardButton("🇬🇧 English")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text("⬇️ Виберіть мову / Choose language:", reply_markup=reply_markup)
            return

        # Get user language
        lang = coordinator.user_languages[user_id]
        logger.info(f"User {user_id} language: {lang}")

        # FIX 2: Proper menu command handling
        if is_menu_command(text):
            await handle_menu_commands(update, context, text, lang, user_id)
        else:
            # Handle user states
            await handle_user_states(update, context, text, lang, user_id)

    except Exception as e:
        logger.error(f"Critical error in handle_message: {e}")
        await handle_critical_error(update, context, user_id)


async def handle_menu_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int):
    """Handle menu commands"""
    logger.info(f"Processing menu command: {text}")

    # MAIN MENU COMMANDS PROCESSING
    if text in ["📊 Аналітик", "📊 Analyst"]:
        logger.info("Navigating to analyst menu")
        coordinator.user_states[user_id] = None
        await show_analyst_menu(update, context, lang)

    elif text in ["🍎 Дієтолог", "🍎 Dietitian"]:
        logger.info("Navigating to dietitian menu")
        coordinator.user_states[user_id] = None
        await show_dietitian_menu(update, context, lang)

    # ANALYST FUNCTIONS
    elif text in ["➕ Додати їжу", "➕ Add food"]:
        logger.info("Starting food addition")
        coordinator.user_states[user_id] = "waiting_meal_type"

        if lang == "uk":
            keyboard = [["🌅 Сніданок", "🌞 Обід"], ["🌙 Вечеря", "🍪 Перекус"], ["⬅️ Назад"]]
            text_msg = "🍽 Оберіть тип прийому їжі:"
        else:
            keyboard = [["🌅 Breakfast", "🌞 Lunch"], ["🌙 Dinner", "🍪 Snack"], ["⬅️ Back"]]
            text_msg = "🍽 Choose meal type:"

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(text_msg, reply_markup=reply_markup)

    elif text in ["📊 Підсумок дня", "📊 Daily summary"]:
        logger.info("Requesting daily report")
        result = await coordinator.route_request(user_id, "daily_summary", {"lang": lang})
        await send_result(update, result, lang)

    elif text in ["🗑️ Видалити їжу", "🗑️ Delete food"]:
        logger.info("Deleting food")
        result = await coordinator.route_request(user_id, "delete_food", {"lang": lang})
        await send_result(update, result, lang)

    # DIETITIAN FUNCTIONS
    elif text in ["🧮 Розрахувати калораж", "🧮 Calculate calories"]:
        logger.info("Starting calorie calculation")
        coordinator.user_states[user_id] = "calorie_calc_age"
        await update.message.reply_text(
            "👤 Введіть ваш вік (число):" if lang == "uk" else "👤 Enter your age (number):"
        )

    elif text in ["💡 Рекомендації", "💡 Recommendations"]:
        logger.info("Requesting recommendations")
        result = await coordinator.route_request(user_id, "get_recommendations", {"lang": lang})
        await send_result(update, result, lang)

    elif text in ["📋 Мій профіль", "📋 My profile"]:
        logger.info("Showing profile")
        result = await coordinator.route_request(user_id, "show_profile", {"lang": lang})
        await send_result(update, result, lang)

    # "BACK" BUTTON
    elif text in ["⬅️ Назад", "⬅️ Back"]:
        logger.info("Going back")
        coordinator.user_states[user_id] = None
        await show_main_menu(update, context)


async def handle_user_states(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int):
    """Handle user states"""
    current_state = coordinator.user_states.get(user_id)
    logger.info(f"Processing state: {current_state}")

    if current_state == "waiting_meal_type":
        logger.info(f"Food type selection: {text}")
        meal_types_uk = ["🌅 Сніданок", "🌞 Обід", "🌙 Вечеря", "🍪 Перекус"]
        meal_types_en = ["🌅 Breakfast", "🌞 Lunch", "🌙 Dinner", "🍪 Snack"]

        if text in meal_types_uk or text in meal_types_en:
            coordinator.user_states[f"{user_id}_meal_type"] = text
            coordinator.user_states[user_id] = "waiting_food"
            await update.message.reply_text(
                "🍽 Опишіть що ви їли:" if lang == "uk" else "🍽 Describe what you ate:"
            )
        else:
            await update.message.reply_text("❌ Оберіть тип їжі" if lang == "uk" else "❌ Select meal type")

    elif current_state == "waiting_food":
        logger.info(f"Food description: {text}")
        meal_type = coordinator.user_states.get(f"{user_id}_meal_type", "")
        meal_desc = f"{meal_type}: {text}" if meal_type else text

        result = await coordinator.route_request(user_id, "add_meal", {"meal_desc": meal_desc, "lang": lang})

        # Clear state
        coordinator.user_states[user_id] = None
        if f"{user_id}_meal_type" in coordinator.user_states:
            del coordinator.user_states[f"{user_id}_meal_type"]

        await send_result(update, result, lang)
        await show_analyst_menu(update, context, lang)

    elif current_state == "calorie_calc_age":
        # Handle age input for calorie calculation
        try:
            age = int(text)
            coordinator.user_states[f"{user_id}_age"] = age
            coordinator.user_states[user_id] = "calorie_calc_weight"
            await update.message.reply_text(
                "⚖️ Введіть вашу вагу (кг):" if lang == "uk" else "⚖️ Enter your weight (kg):"
            )
        except ValueError:
            await update.message.reply_text(
                "❌ Введіть число (наприклад: 25)" if lang == "uk" else "❌ Enter a number (e.g.: 25)"
            )

    else:
        # Unknown command
        logger.info(f"Unknown command: {text}")
        error_msg = "❌ Невідома команда. Повертаємось до меню." if lang == "uk" else "❌ Unknown command. Returning to menu."
        await update.message.reply_text(error_msg)
        await show_main_menu(update, context)


async def handle_critical_error(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Handle critical errors"""
    try:
        lang = coordinator.user_languages.get(user_id, "uk")
        error_msg = "❌ Сталася помилка. Повертаємось до меню." if lang == "uk" else "❌ An error occurred. Returning to menu."
        await update.message.reply_text(error_msg)
        await show_main_menu(update, context)
    except Exception as e2:
        logger.error(f"Error handling error: {e2}")


# ============================================================================
# BOT STARTUP
# ============================================================================

def main():
    """Start the bot"""
    logger.info("🚀 Starting bot...")

    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN not found in .env file!")
        print("Set TELEGRAM_TOKEN in .env file")
        return

    logger.info(f"Token found: {TOKEN[:10]}...")

    try:
        app = ApplicationBuilder().token(TOKEN).build()
        logger.info("Application created")

        # FIXED error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Bot error: {context.error}")

            if update and update.effective_user:
                user_id = update.effective_user.id
                lang = coordinator.user_languages.get(user_id, "uk")

                # Clear user state
                coordinator.user_states[user_id] = None

                try:
                    error_msg = "❌ Сталася технічна помилка. Спробуйте ще раз." if lang == "uk" else "❌ Technical error occurred. Please try again."
                    if update.message:
                        await update.message.reply_text(error_msg)
                        await show_main_menu(update, context)
                except:
                    logger.error("Failed to send error message")

        app.add_error_handler(error_handler)

        # FIXED handler registration
        app.add_handler(CommandHandler("start", start))
        # Remove separate language handler - it's now in handle_message
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Handlers registered")

        # Start bot
        logger.info("Bot starting...")
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Critical startup error: {e}")
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    main()
