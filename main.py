# main.py - FINAL COMPLETE VERSION WITH BUTTON DELETION
import os
import logging
from typing import Dict, List
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import multi-agent system
try:
    from multiagent_core import SimpleCoordinator
    logger.info("MultiAgent system loaded")
except ImportError as e:
    logger.error(f"Error importing multiagent_core: {e}")

    class SimpleCoordinator:
        def __init__(self):
            self.user_languages = {}
            self.user_states = {}

        async def route_request(self, user_id, action, data):
            return {"status": "success", "message": f"Test: {action}"}

load_dotenv()
coordinator = SimpleCoordinator()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def user_has_language(user_id: int) -> bool:
    return user_id in coordinator.user_languages

def is_language_command(text: str) -> bool:
    return text in ["🇺🇦 Українська", "🇬🇧 English"]

def is_main_menu_command(text: str) -> bool:
    """Main menu commands - WITHOUT deletion buttons"""
    commands = [
        "📊 Аналітик", "📊 Analyst", "🍎 Дієтолог", "🍎 Dietitian",
        "➕ Додати їжу", "➕ Add food", "🗑️ Видалити їжу", "🗑️ Delete food",
        "📊 Підсумок дня", "📊 Daily summary", "🧮 Розрахувати калораж",
        "🧮 Calculate calories", "💡 Рекомендації", "💡 Recommendations",
        "📋 Мій профіль", "📋 My profile", "⬅️ Назад", "⬅️ Back"
    ]
    return text in commands

def is_delete_button(text: str) -> bool:
    """Check deletion button"""
    # Looking for pattern: starts with emoji (🌅🌞🌙🍪) and contains calories
    import re
    return bool(re.match(r'^[🌅🌞🌙🍪].*\(\d+\s*(ккал|kcal)\)$', text))

# ============================================================================
# MENUS
# ============================================================================

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = coordinator.user_languages.get(user_id, "uk")

    if lang == "uk":
        keyboard = [["📊 Аналітик", "🍎 Дієтолог"]]
        text = "🏠 Головне меню\n\n📊 Аналітик - підрахунок КБЖУ\n🍎 Дієтолог - рекомендації"
    else:
        keyboard = [["📊 Analyst", "🍎 Dietitian"]]
        text = "🏠 Main Menu\n\n📊 Analyst - KBJU calculation\n🍎 Dietitian - recommendations"

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def show_analyst_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    if lang == "uk":
        keyboard = [
            ["➕ Додати їжу", "🗑️ Видалити їжу"],
            ["📊 Підсумок дня"],
            ["⬅️ Назад"]
        ]
        text = "📊 Аналітик\n\nОберіть дію:"
    else:
        keyboard = [
            ["➕ Add food", "🗑️ Delete food"],
            ["📊 Daily summary"],
            ["⬅️ Back"]
        ]
        text = "📊 Analyst\n\nChoose action:"

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def show_dietitian_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    if lang == "uk":
        keyboard = [
            ["🧮 Розрахувати калораж", "💡 Рекомендації"],
            ["📋 Мій профіль", "⬅️ Назад"]
        ]
        text = "🍎 Дієтолог\n\nОберіть дію:"
    else:
        keyboard = [
            ["🧮 Calculate calories", "💡 Recommendations"],
            ["📋 My profile", "⬅️ Back"]
        ]
        text = "🍎 Dietitian\n\nChoose action:"

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(text, reply_markup=reply_markup)

# ============================================================================
# RESULT HANDLER - COMPLETELY FIXED
# ============================================================================

async def send_result(update: Update, result: Dict, lang: str):
    """COMPLETELY FIXED result sender"""
    logger.info(f"Sending result: {result}")

    try:
        status = result.get("status", "unknown")

        if status == "success":
            # 1. KBJU result (food addition)
            if "kbju" in result:
                kbju = result["kbju"]
                if lang == "uk":
                    message = f"""✅ Страву додано!

📊 Калорії: {kbju.get('calories', 0)} ккал
🥩 Білки: {kbju.get('protein', 0)} г  
🧈 Жири: {kbju.get('fat', 0)} г
🍞 Вуглеводи: {kbju.get('carbs', 0)} г

💬 {kbju.get('analysis', '')}"""
                else:
                    message = f"""✅ Meal added!

📊 Calories: {kbju.get('calories', 0)} kcal
🥩 Protein: {kbju.get('protein', 0)} g
🧈 Fat: {kbju.get('fat', 0)} g
🍞 Carbs: {kbju.get('carbs', 0)} g

💬 {kbju.get('analysis', '')}"""

            # 2. Dish list for deletion WITH BUTTONS
            elif "entries" in result and result.get("action") == "show_delete_list":
                entries = result["entries"]

                # Save for deletion
                coordinator.user_states[update.effective_user.id] = "waiting_delete_choice"
                coordinator.user_states[f"{update.effective_user.id}_delete_entries"] = entries

                if lang == "uk":
                    message = "🗑️ Виберіть страву для видалення:"
                    keyboard = []
                    for entry_data in entries:
                        entry = entry_data["entry"]
                        # Create SIMPLE buttons without numbers
                        button_text = f"{entry['description']} ({entry['calories']} ккал)"
                        # Trim if too long
                        if len(button_text) > 50:
                            description = entry['description'][:35] + "..."
                            button_text = f"{description} ({entry['calories']} ккал)"
                        keyboard.append([KeyboardButton(button_text)])
                    keyboard.append([KeyboardButton("⬅️ Назад")])
                else:
                    message = "🗑️ Choose meal to delete:"
                    keyboard = []
                    for entry_data in entries:
                        entry = entry_data["entry"]
                        button_text = f"{entry['description']} ({entry['calories']} kcal)"
                        if len(button_text) > 50:
                            description = entry['description'][:35] + "..."
                            button_text = f"{description} ({entry['calories']} kcal)"
                        keyboard.append([KeyboardButton(button_text)])
                    keyboard.append([KeyboardButton("⬅️ Back")])

                try:
                    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                    await update.message.reply_text(message, reply_markup=reply_markup)
                    logger.info("Delete buttons sent")
                    return
                except Exception as e:
                    logger.error(f"Error with buttons: {e}")
                    # Fallback without buttons
                    message += "\n\n"
                    for i, entry_data in enumerate(entries):
                        entry = entry_data["entry"]
                        message += f"{i + 1}. {entry['description']} ({entry['calories']} ккал)\n"

            # 3. Daily report
            elif "summary" in result:
                message = result["summary"]

            # 4. Recommendations
            elif "recommendations" in result:
                message = result["recommendations"]

            # 5. User profile
            elif "profile" in result:
                profile = result["profile"]
                calories = profile.get("calories", {})
                if lang == "uk":
                    message = f"""📋 Ваш профіль:

👤 Дані:
• Вік: {profile.get('age')} років
• Вага: {profile.get('weight')} кг
• Зріст: {profile.get('height')} см
• Стать: {"жінка" if profile.get('gender') == 'female' else "чоловік"}

📊 Денний калораж:
• Підтримання ваги: {calories.get('maintain', 'N/A')} ккал/день
• Для схуднення: {calories.get('lose', 'N/A')} ккал/день
• Для набору ваги: {calories.get('gain', 'N/A')} ккал/день

🕐 Оновлено: {profile.get('updated_at', 'N/A')[:16].replace('T', ' ')}"""
                else:
                    message = f"""📋 Your profile:

👤 Data:
• Age: {profile.get('age')} years
• Weight: {profile.get('weight')} kg
• Height: {profile.get('height')} cm
• Gender: {profile.get('gender')}

📊 Daily calories:
• Maintain: {calories.get('maintain', 'N/A')} kcal/day
• Lose: {calories.get('lose', 'N/A')} kcal/day
• Gain: {calories.get('gain', 'N/A')} kcal/day

🕐 Updated: {profile.get('updated_at', 'N/A')[:16].replace('T', ' ')}"""

            # 6. Calorie calculation result
            elif "calories" in result:
                calories = result["calories"]
                user_data = result.get("user_data", {})
                if lang == "uk":
                    message = f"""🧮 Розрахунок калорій завершено!

👤 Ваші дані:
• Вік: {user_data.get('age')} років
• Вага: {user_data.get('weight')} кг
• Зріст: {user_data.get('height')} см
• Стать: {"жінка" if user_data.get('gender') == 'female' else "чоловік"}

📊 Результати:
• Базовий метаболізм: {calories['bmr']} ккал/день
• Підтримання ваги: {calories['maintain']} ккал/день
• Для схуднення: {calories['lose']} ккал/день
• Для набору ваги: {calories['gain']} ккал/день

✅ Профіль збережено!"""
                else:
                    message = f"""🧮 Calorie calculation completed!

👤 Your data:
• Age: {user_data.get('age')} years
• Weight: {user_data.get('weight')} kg
• Height: {user_data.get('height')} cm
• Gender: {user_data.get('gender')}

📊 Results:
• Basal metabolism: {calories['bmr']} kcal/day
• Maintain weight: {calories['maintain']} kcal/day
• Lose weight: {calories['lose']} kcal/day
• Gain weight: {calories['gain']} kcal/day

✅ Profile saved!"""

            # 7. Regular message
            else:
                message = result.get("message", "✅ Готово!" if lang == "uk" else "✅ Done!")

        elif status == "error":
            message = f"❌ {result.get('message', 'Помилка' if lang == 'uk' else 'Error')}"

        elif status == "no_data":
            if lang == "uk":
                message = "📭 Немає даних за сьогодні\n\nДодайте спочатку їжу через 'Додати їжу'"
            else:
                message = "📭 No data for today\n\nAdd food first through 'Add food'"

        elif status == "no_profile":
            if lang == "uk":
                message = "❌ Профіль не знайдено\n\nСпочатку розрахуйте калораж через 'Дієтолог' → 'Розрахувати калораж'"
            else:
                message = "❌ Profile not found\n\nCalculate calories first through 'Dietitian' → 'Calculate calories'"

        else:
            message = result.get("message", str(result))

        # Send message
        await update.message.reply_text(message)
        logger.info("Result sent successfully")

    except Exception as e:
        logger.error(f"Error in send_result: {e}")
        error_msg = "❌ Помилка" if lang == "uk" else "❌ Error"
        try:
            await update.message.reply_text(error_msg)
        except:
            logger.error("Failed to send error message")

# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start from user {update.effective_user.id}")

    keyboard = [
        [KeyboardButton("🇺🇦 Українська")],
        [KeyboardButton("🇬🇧 English")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⬇️ Виберіть мову / Choose language:", reply_markup=reply_markup)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if "Українська" in text:
        coordinator.user_languages[user_id] = "uk"
        await update.message.reply_text("✅ Мову встановлено: українська")
        await show_main_menu(update, context)
    elif "English" in text:
        coordinator.user_languages[user_id] = "en"
        await update.message.reply_text("✅ Language set to: English")
        await show_main_menu(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MAIN MESSAGE HANDLER"""
    user_id = update.effective_user.id
    text = update.message.text
    current_state = coordinator.user_states.get(user_id)

    logger.info(f"User {user_id}: '{text}' (state: {current_state})")

    try:
        # 1. Check language
        if not user_has_language(user_id):
            if is_language_command(text):
                await set_language(update, context)
                return
            else:
                keyboard = [[KeyboardButton("🇺🇦 Українська")], [KeyboardButton("🇬🇧 English")]]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text("⬇️ Виберіть мову / Choose language:", reply_markup=reply_markup)
                return

        lang = coordinator.user_languages[user_id]

        # 2. PRIORITY: user states
        if current_state == "waiting_meal_type":
            await handle_meal_type_selection(update, context, text, lang, user_id)
            return

        elif current_state == "waiting_food":
            await handle_food_description(update, context, text, lang, user_id)
            return

        elif current_state == "waiting_delete_choice":
            await handle_delete_choice(update, context, text, lang, user_id)
            return

        elif current_state and current_state.startswith("calorie_calc"):
            await handle_calorie_calculation(update, context, text, lang, user_id, current_state)
            return

        # 3. Menu commands
        elif is_main_menu_command(text):
            await handle_menu_command(update, context, text, lang, user_id)
            return

        # 4. Unknown command
        else:
            await handle_unknown(update, context, text, lang)

    except Exception as e:
        logger.error(f"Critical error: {e}")
        await handle_error(update, context, user_id)

# ============================================================================
# SPECIFIC HANDLERS
# ============================================================================

async def handle_meal_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int):
    meal_types = ["🌅 Сніданок", "🌞 Обід", "🌙 Вечеря", "🍪 Перекус",
                  "🌅 Breakfast", "🌞 Lunch", "🌙 Dinner", "🍪 Snack"]

    if text in meal_types:
        logger.info(f"Meal type selected: {text}")
        coordinator.user_states[f"{user_id}_meal_type"] = text
        coordinator.user_states[user_id] = "waiting_food"

        msg = "🍽️ Опишіть що ви їли:" if lang == "uk" else "🍽️ Describe what you ate:"
        await update.message.reply_text(msg)
    else:
        msg = "❌ Оберіть тип їжі" if lang == "uk" else "❌ Select meal type"
        await update.message.reply_text(msg)

async def handle_food_description(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int):
    logger.info(f"Food description: {text}")

    meal_type = coordinator.user_states.get(f"{user_id}_meal_type", "")
    meal_desc = f"{meal_type}: {text}" if meal_type else text

    # Clear states
    coordinator.user_states[user_id] = None
    coordinator.user_states.pop(f"{user_id}_meal_type", None)

    # Process food
    result = await coordinator.route_request(user_id, "add_meal", {"meal_desc": meal_desc, "lang": lang})
    await send_result(update, result, lang)
    await show_analyst_menu(update, context, lang)

async def handle_delete_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int):
    """NEW LOGIC for deletion through buttons"""

    # Back button
    if text in ["⬅️ Назад", "⬅️ Back"]:
        logger.info("Back button pressed during deletion")
        coordinator.user_states[user_id] = None
        coordinator.user_states.pop(f"{user_id}_delete_entries", None)
        await show_analyst_menu(update, context, lang)
        return

    # Search dish by button text
    entries = coordinator.user_states.get(f"{user_id}_delete_entries", [])

    if entries:
        # Search entry by button content
        selected_entry = None
        selected_index = None

        for entry_data in entries:
            entry = entry_data["entry"]
            # Check if dish description is contained in button text
            if entry['description'] in text and str(entry['calories']) in text:
                selected_entry = entry
                selected_index = entry_data["index"]
                break

        if selected_entry and selected_index is not None:
            logger.info(f"Found meal to delete: {selected_entry['description']}")

            # Delete dish
            result = await coordinator.route_request(user_id, "confirm_delete", {"index": selected_index, "lang": lang})

            # Clear state
            coordinator.user_states[user_id] = None
            coordinator.user_states.pop(f"{user_id}_delete_entries", None)

            await send_result(update, result, lang)
            await show_analyst_menu(update, context, lang)
        else:
            logger.warning(f"Could not find meal to delete: {text}")
            msg = "❌ Страву не знайдено. Оберіть з списку." if lang == "uk" else "❌ Meal not found. Choose from list."
            await update.message.reply_text(msg)
    else:
        msg = "❌ Список порожній" if lang == "uk" else "❌ List is empty"
        await update.message.reply_text(msg)

async def handle_calorie_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int, current_state: str):
    """Handle calorie calculation"""

    if current_state == "calorie_calc_age":
        try:
            age = int(text)
            coordinator.user_states[f"{user_id}_age"] = age
            coordinator.user_states[user_id] = "calorie_calc_weight"
            msg = "⚖️ Введіть вашу вагу (кг):" if lang == "uk" else "⚖️ Enter your weight (kg):"
            await update.message.reply_text(msg)
        except ValueError:
            msg = "❌ Введіть число (наприклад: 25)" if lang == "uk" else "❌ Enter a number (e.g.: 25)"
            await update.message.reply_text(msg)

    elif current_state == "calorie_calc_weight":
        try:
            weight = float(text)
            coordinator.user_states[f"{user_id}_weight"] = weight
            coordinator.user_states[user_id] = "calorie_calc_height"
            msg = "📏 Введіть ваш зріст (см):" if lang == "uk" else "📏 Enter your height (cm):"
            await update.message.reply_text(msg)
        except ValueError:
            msg = "❌ Введіть число (наприклад: 70)" if lang == "uk" else "❌ Enter a number (e.g.: 70)"
            await update.message.reply_text(msg)

    elif current_state == "calorie_calc_height":
        try:
            height = int(text)
            coordinator.user_states[f"{user_id}_height"] = height
            coordinator.user_states[user_id] = "calorie_calc_gender"

            if lang == "uk":
                keyboard = [["👨 Чоловік", "👩 Жінка"], ["⬅️ Назад"]]
                text_msg = "👤 Оберіть стать:"
            else:
                keyboard = [["👨 Male", "👩 Female"], ["⬅️ Back"]]
                text_msg = "👤 Choose gender:"

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(text_msg, reply_markup=reply_markup)
        except ValueError:
            msg = "❌ Введіть число (наприклад: 175)" if lang == "uk" else "❌ Enter a number (e.g.: 175)"
            await update.message.reply_text(msg)

    elif current_state == "calorie_calc_gender":
        gender_map = {"👨 Чоловік": "male", "👩 Жінка": "female", "👨 Male": "male", "👩 Female": "female"}

        if text in gender_map:
            coordinator.user_states[f"{user_id}_gender"] = gender_map[text]
            coordinator.user_states[user_id] = "calorie_calc_activity"

            if lang == "uk":
                keyboard = [
                    ["🛋 Сидячий спосіб життя"],
                    ["🚶 Легка активність"],
                    ["🏃 Помірна активність"],
                    ["💪 Висока активність"],
                    ["⬅️ Назад"]
                ]
                text_msg = "🏃 Оберіть рівень активності:"
            else:
                keyboard = [
                    ["🛋 Sedentary lifestyle"],
                    ["🚶 Light activity"],
                    ["🏃 Moderate activity"],
                    ["💪 High activity"],
                    ["⬅️ Back"]
                ]
                text_msg = "🏃 Choose activity level:"

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(text_msg, reply_markup=reply_markup)
        else:
            msg = "❌ Оберіть стать" if lang == "uk" else "❌ Choose gender"
            await update.message.reply_text(msg)

    elif current_state == "calorie_calc_activity":
        activity_map = {
            "🛋 Сидячий спосіб життя": 1.2, "🚶 Легка активність": 1.375,
            "🏃 Помірна активність": 1.55, "💪 Висока активність": 1.725,
            "🛋 Sedentary lifestyle": 1.2, "🚶 Light activity": 1.375,
            "🏃 Moderate activity": 1.55, "💪 High activity": 1.725
        }

        if text in activity_map:
            # Collect all data
            age = coordinator.user_states.get(f"{user_id}_age")
            weight = coordinator.user_states.get(f"{user_id}_weight")
            height = coordinator.user_states.get(f"{user_id}_height")
            gender = coordinator.user_states.get(f"{user_id}_gender")

            if all([age, weight, height, gender]):
                user_data = {
                    "age": age,
                    "weight": weight,
                    "height": height,
                    "gender": gender,
                    "activity_coefficient": activity_map[text]
                }

                # Clear states
                coordinator.user_states[user_id] = None
                for key in [f"{user_id}_age", f"{user_id}_weight", f"{user_id}_height", f"{user_id}_gender"]:
                    coordinator.user_states.pop(key, None)

                # Calculate calories
                result = await coordinator.route_request(user_id, "calculate_calories", {"user_data": user_data})
                await send_result(update, result, lang)
                await show_dietitian_menu(update, context, lang)
            else:
                msg = "❌ Помилка даних" if lang == "uk" else "❌ Data error"
                await update.message.reply_text(msg)
        else:
            msg = "❌ Оберіть активність" if lang == "uk" else "❌ Choose activity"
            await update.message.reply_text(msg)

async def handle_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int):
    """Handle menu commands"""
    logger.info(f"Menu command: {text}")

    # Clear states
    coordinator.user_states[user_id] = None

    if text in ["📊 Аналітик", "📊 Analyst"]:
        await show_analyst_menu(update, context, lang)

    elif text in ["🍎 Дієтолог", "🍎 Dietitian"]:
        await show_dietitian_menu(update, context, lang)

    elif text in ["➕ Додати їжу", "➕ Add food"]:
        coordinator.user_states[user_id] = "waiting_meal_type"

        if lang == "uk":
            keyboard = [["🌅 Сніданок", "🌞 Обід"], ["🌙 Вечеря", "🍪 Перекус"], ["⬅️ Назад"]]
            msg = "🍽️ Оберіть тип прийому їжі:"
        else:
            keyboard = [["🌅 Breakfast", "🌞 Lunch"], ["🌙 Dinner", "🍪 Snack"], ["⬅️ Back"]]
            msg = "🍽️ Choose meal type:"

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(msg, reply_markup=reply_markup)

    elif text in ["📊 Підсумок дня", "📊 Daily summary"]:
        result = await coordinator.route_request(user_id, "daily_summary", {"lang": lang})
        await send_result(update, result, lang)

    elif text in ["🗑️ Видалити їжу", "🗑️ Delete food"]:
        result = await coordinator.route_request(user_id, "delete_meal", {"lang": lang})
        await send_result(update, result, lang)

    elif text in ["🧮 Розрахувати калораж", "🧮 Calculate calories"]:
        coordinator.user_states[user_id] = "calorie_calc_age"
        msg = "👤 Введіть ваш вік (число):" if lang == "uk" else "👤 Enter your age (number):"
        await update.message.reply_text(msg)

    elif text in ["💡 Рекомендації", "💡 Recommendations"]:
        result = await coordinator.route_request(user_id, "get_recommendations", {"lang": lang})
        await send_result(update, result, lang)

    elif text in ["📋 Мій профіль", "📋 My profile"]:
        result = await coordinator.route_request(user_id, "show_profile", {"lang": lang})
        await send_result(update, result, lang)

    elif text in ["⬅️ Назад", "⬅️ Back"]:
        await show_main_menu(update, context)

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str):
    """Handle unknown commands"""
    logger.info(f"Unknown: {text}")
    msg = "❌ Невідома команда" if lang == "uk" else "❌ Unknown command"
    await update.message.reply_text(msg)
    await show_main_menu(update, context)

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Handle errors"""
    try:
        lang = coordinator.user_languages.get(user_id, "uk")
        msg = "❌ Помилка" if lang == "uk" else "❌ Error"
        await update.message.reply_text(msg)
        coordinator.user_states[user_id] = None
        await show_main_menu(update, context)
    except:
        logger.error("Failed to handle error")

# ============================================================================
# BOT STARTUP
# ============================================================================

def main():
    """Start bot"""
    logger.info("Starting bot...")

    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("TELEGRAM_TOKEN not found in .env!")
        return

    logger.info(f"Token: {TOKEN[:10]}...")

    try:
        app = ApplicationBuilder().token(TOKEN).build()

        # Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Bot error: {context.error}")

        app.add_error_handler(error_handler)

        logger.info("Bot starting...")
        print("Bot running! Press Ctrl+C to stop.")
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Startup error: {e}")
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
