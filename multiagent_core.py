import json
from datetime import datetime, date
from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path

# Data path definition
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"

# ============================================================================
# Import original functions
# ============================================================================

try:
    from agents.analyst_agent import estimate_kbju, analyze_daily_nutrition
    from agents.dietitian_agent import calculate_daily_calories, get_nutrition_advice, load_user_profile

    USE_ORIGINAL_FUNCTIONS = True
except ImportError:
    USE_ORIGINAL_FUNCTIONS = False


    def estimate_kbju(food_description: str, lang: str = "uk") -> dict:
        return {
            "calories": 0,
            "protein": 0,
            "fat": 0,
            "carbs": 0,
            "analysis": "❌ GPT недоступний. Необхідно налаштувати OpenAI API"
            if lang == "uk" else "❌ GPT unavailable. OpenAI API setup required"
        }


    def calculate_daily_calories(age: int, gender: str, weight: float, height: int,
                                 activity_coefficient: float) -> dict:
        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        total_calories = bmr * activity_coefficient

        return {
            "bmr": round(bmr),
            "total": round(total_calories),
            "maintain": round(total_calories),
            "lose": round(total_calories - 300),
            "gain": round(total_calories + 300)
        }


    def get_nutrition_advice(profile: dict, lang: str = "uk") -> str:
        calories = profile.get('calories', {})
        maintain_calories = calories.get('maintain', 2000)

        if lang == "uk":
            return f"""💡 Базові рекомендації (без GPT):

🎯 Ваша денна норма: {maintain_calories} ккал

❌ Для персональних рекомендацій потрібен OpenAI API
💡 Налаштуйте OPENAI_API_KEY в .env файлі"""
        else:
            return f"""💡 Basic recommendations (without GPT):

🎯 Your daily target: {maintain_calories} kcal

❌ For personalized recommendations OpenAI API is required
💡 Set OPENAI_API_KEY in .env file"""


    def load_user_profile(user_id: int) -> dict:
        try:
            profile_file = DATA_DIR / "profiles.json"
            with open(profile_file, "r", encoding="utf-8") as f:
                profiles = json.load(f)
            return profiles.get(str(user_id))
        except FileNotFoundError:
            return None


# ============================================================================
# Communication protocol
# ============================================================================

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    content: Dict
    timestamp: datetime


class SimpleMessageBus:
    def __init__(self):
        self.messages: Dict[str, List[AgentMessage]] = {}

    async def send_message(self, sender: str, receiver: str, content: Dict):
        if receiver not in self.messages:
            self.messages[receiver] = []

        message = AgentMessage(sender, receiver, content, datetime.now())
        self.messages[receiver].append(message)

    async def get_messages(self, agent_id: str) -> List[AgentMessage]:
        messages = self.messages.get(agent_id, [])
        self.messages[agent_id] = []
        return messages


# ============================================================================
# Base agent
# ============================================================================

class SimpleAgent:
    def __init__(self, agent_id: str, name: str, message_bus: SimpleMessageBus):
        self.agent_id = agent_id
        self.name = name
        self.message_bus = message_bus
        self.is_active = True

    async def send_to_agent(self, target: str, message_type: str, data: Dict):
        await self.message_bus.send_message(
            self.agent_id,
            target,
            {"type": message_type, "data": data}
        )

    async def process_messages(self):
        messages = await self.message_bus.get_messages(self.agent_id)
        for message in messages:
            await self.handle_message(message)

    async def handle_message(self, message: AgentMessage):
        pass


# ============================================================================
# Analyst agent
# ============================================================================

class AnalystAgent(SimpleAgent):
    def __init__(self, message_bus: SimpleMessageBus):
        super().__init__("analyst", "📊 Аналітик", message_bus)
        self.user_patterns = {}

    async def add_meal(self, user_id: int, meal_desc: str, lang: str):
        try:
            if not USE_ORIGINAL_FUNCTIONS:
                error_msg = "❌ GPT недоступний. Потрібен OpenAI API ключ" \
                    if lang == "uk" else "❌ GPT unavailable. OpenAI API key required"
                return {"status": "error", "message": error_msg}

            kbju = estimate_kbju(meal_desc, lang)
            self._save_entry(meal_desc, kbju)
            await self._autonomous_analysis(user_id, kbju, meal_desc)

            await self.send_to_agent("dietitian", "meal_added", {
                "user_id": user_id,
                "meal": meal_desc,
                "kbju": kbju,
                "analysis": self._quick_meal_assessment(kbju)
            })

            return {"status": "success", "kbju": kbju}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _save_entry(self, description: str, kbju: dict):
        try:
            DATA_DIR.mkdir(exist_ok=True)
            data_file = DATA_DIR / "nutrition_data.json"

            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = []
            except json.JSONDecodeError:
                data = []

            entry = {
                "date": date.today().strftime("%Y-%m-%d"),
                "description": description,
                "calories": kbju.get("calories", 0),
                "protein": kbju.get("protein", 0),
                "fat": kbju.get("fat", 0),
                "carbs": kbju.get("carbs", 0),
                "timestamp": datetime.now().isoformat()
            }
            data.append(entry)

            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            raise

    async def get_daily_summary(self, user_id: int, lang: str):
        today = date.today()
        entries = self._get_entries_for_date(today)

        if entries:
            total_calories = sum(entry.get('calories', 0) for entry in entries)

            await self.send_to_agent("dietitian", "analyze_day", {
                "user_id": user_id,
                "entries": entries,
                "total_calories": total_calories,
                "lang": lang
            })

            summary = self._format_summary(entries, lang)
            return {"status": "success", "entries": entries, "summary": summary}
        else:
            no_data_msg = "Немає даних за день" if lang == "uk" else "No data for today"
            return {"status": "no_data", "message": no_data_msg}

    def _format_summary(self, entries: list, lang: str) -> str:
        total_calories = sum(entry.get('calories', 0) for entry in entries)
        total_protein = sum(entry.get('protein', 0) for entry in entries)
        total_fat = sum(entry.get('fat', 0) for entry in entries)
        total_carbs = sum(entry.get('carbs', 0) for entry in entries)

        if lang == "uk":
            summary = f"""📊 **Підсумок за день:**

🍽 **Прийомів їжі:** {len(entries)}

📈 **Загальні показники:**
• Калорії: {total_calories} ккал
• Білки: {total_protein} г
• Жири: {total_fat} г
• Вуглеводи: {total_carbs} г

📋 **Список страв:**"""
        else:
            summary = f"""📊 **Daily Summary:**

🍽 **Meals:** {len(entries)}

📈 **Total indicators:**
• Calories: {total_calories} kcal
• Protein: {total_protein} g
• Fat: {total_fat} g
• Carbs: {total_carbs} g

📋 **Meal list:**"""

        for entry in entries:
            summary += f"\n• {entry['description']} ({entry['calories']} ккал)"

        return summary

    def _get_entries_for_date(self, target_date):
        try:
            data_file = DATA_DIR / "nutrition_data.json"
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = []
            for entry in data:
                try:
                    entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                    if entry_date == target_date:
                        result.append(entry)
                except (KeyError, ValueError):
                    continue
            return result
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    async def delete_meal(self, user_id: int, lang: str):
        today = date.today()
        entries = self._get_entries_for_date(today)

        if not entries:
            no_data_msg = "Немає записів для видалення" if lang == "uk" else "No entries to delete"
            return {"status": "no_data", "message": no_data_msg}

        entries_with_index = []
        try:
            data_file = DATA_DIR / "nutrition_data.json"
            with open(data_file, "r", encoding="utf-8") as f:
                all_data = json.load(f)

            for global_index, entry in enumerate(all_data):
                try:
                    entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                    if entry_date == today:
                        entries_with_index.append({"entry": entry, "index": global_index})
                except (KeyError, ValueError):
                    continue

        except Exception as e:
            return {"status": "error",
                    "message": "Помилка підготовки списку" if lang == "uk" else "Error preparing list"}

        return {"status": "success", "entries": entries_with_index, "action": "show_delete_list"}

    async def confirm_delete_meal(self, user_id: int, entry_index: int, lang: str):
        try:
            deleted_entry = self._delete_entry_by_index(entry_index)
            if deleted_entry:
                await self.send_to_agent("dietitian", "meal_deleted", {
                    "user_id": user_id,
                    "deleted_entry": deleted_entry
                })

                success_msg = f"Запис видалено: {deleted_entry['description']}" if lang == "uk" else f"Entry deleted: {deleted_entry['description']}"
                return {"status": "success", "message": success_msg}
            else:
                error_msg = "Помилка при видаленні" if lang == "uk" else "Error deleting entry"
                return {"status": "error", "message": error_msg}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _delete_entry_by_index(self, index):
        try:
            data_file = DATA_DIR / "nutrition_data.json"
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if 0 <= index < len(data):
                deleted_entry = data.pop(index)
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return deleted_entry
            return None
        except Exception:
            return None

    async def _autonomous_analysis(self, user_id: int, kbju: Dict, meal_desc: str):
        calories = kbju.get('calories', 0)

        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {"meals": [], "avg_calories": 0}

        self.user_patterns[user_id]["meals"].append({
            "calories": calories,
            "timestamp": datetime.now().isoformat()
        })

        if calories > 800:
            await self.send_to_agent("dietitian", "high_calorie_alert", {
                "user_id": user_id,
                "calories": calories,
                "meal": meal_desc
            })

    def _quick_meal_assessment(self, kbju: Dict) -> str:
        calories = kbju.get('calories', 0)
        if calories < 200:
            return "low_calorie"
        elif calories > 600:
            return "high_calorie"
        else:
            return "normal"

    async def handle_message(self, message: AgentMessage):
        msg_type = message.content.get("type")
        data = message.content.get("data", {})

        if msg_type == "request_nutrition_data":
            user_id = data.get("user_id")
            patterns = self.user_patterns.get(user_id, {})

            await self.send_to_agent("dietitian", "nutrition_data", {
                "user_id": user_id,
                "patterns": patterns
            })


# ============================================================================
# Dietitian agent
# ============================================================================

class DietitianAgent(SimpleAgent):
    def __init__(self, message_bus: SimpleMessageBus):
        super().__init__("dietitian", "🍎 Дієтолог", message_bus)
        self.user_profiles = {}
        self.alerts = {}

    async def calculate_calories(self, user_id: int, user_data: Dict):
        try:
            calories = calculate_daily_calories(
                user_data["age"], user_data["gender"], user_data["weight"],
                user_data["height"], user_data["activity_coefficient"]
            )

            self._save_user_profile(user_id, user_data, calories)

            self.user_profiles[user_id] = {
                "calories": calories,
                "data": user_data,
                "created": datetime.now().isoformat()
            }

            return {"status": "success", "calories": calories, "user_data": user_data}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _save_user_profile(self, user_id: int, data: dict, calories: dict):
        DATA_DIR.mkdir(exist_ok=True)
        profile_file = DATA_DIR / "profiles.json"

        try:
            with open(profile_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    profiles = {}
                else:
                    profiles = json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            profiles = {}

        profiles[str(user_id)] = {
            "age": data["age"],
            "gender": data["gender"],
            "weight": data["weight"],
            "height": data["height"],
            "activity_coefficient": data["activity_coefficient"],
            "calories": calories,
            "updated_at": datetime.now().isoformat()
        }

        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)

    async def get_recommendations(self, user_id: int, lang: str):
        profile = load_user_profile(user_id)
        if not profile:
            return {"status": "no_profile"}

        await self.send_to_agent("analyst", "request_nutrition_data", {
            "user_id": user_id
        })

        nutrition_data = self._get_user_nutrition_data(user_id)

        enhanced_profile = profile.copy()
        if nutrition_data:
            enhanced_profile['recent_nutrition'] = nutrition_data

        if USE_ORIGINAL_FUNCTIONS:
            recommendations = self._get_enhanced_nutrition_advice(enhanced_profile, lang)
        else:
            recommendations = get_nutrition_advice(profile, lang)

        return {"status": "success", "recommendations": recommendations}

    def _get_user_nutrition_data(self, user_id: int) -> str:
        try:
            data_file = DATA_DIR / "nutrition_data.json"
            with open(data_file, "r", encoding="utf-8") as f:
                all_data = json.load(f)

            today = date.today()
            today_str = today.strftime("%Y-%m-%d")

            today_entries = []
            total_calories = 0
            total_protein = 0
            total_fat = 0
            total_carbs = 0

            for entry in all_data:
                try:
                    entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                    if entry_date == today:
                        today_entries.append(entry)
                        total_calories += entry.get("calories", 0)
                        total_protein += entry.get("protein", 0)
                        total_fat += entry.get("fat", 0)
                        total_carbs += entry.get("carbs", 0)
                except (KeyError, ValueError):
                    continue

            if not today_entries:
                return "User hasn't eaten anything today yet."

            nutrition_summary = f"""User's nutrition for TODAY ({today_str}):

TOTAL FOR THE DAY:
• Calories: {total_calories} kcal
• Proteins: {total_protein} g
• Fats: {total_fat} g
• Carbs: {total_carbs} g
• Meals: {len(today_entries)}

DETAILED ALL DISHES TODAY:"""

            for i, entry in enumerate(today_entries, 1):
                nutrition_summary += f"\n{i}. {entry['description']} ({entry['calories']} kcal, {entry['protein']}g protein, {entry['fat']}g fat, {entry['carbs']}g carbs)"

            return nutrition_summary

        except Exception as e:
            return ""

    def _get_enhanced_nutrition_advice(self, enhanced_profile: dict, lang: str) -> str:
        try:
            if 'recent_nutrition' in enhanced_profile and enhanced_profile['recent_nutrition']:
                from openai import OpenAI
                import os

                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

                calories = enhanced_profile.get('calories', {})
                target_calories = calories.get('maintain', 2000)
                today_nutrition = enhanced_profile['recent_nutrition']

                if lang == "uk":
                    prompt = f"""Ти - професійний дієтолог. Проаналізуй що користувач з'їв СЬОГОДНІ і дай персональні рекомендації.

ЦІЛЬОВИЙ КАЛОРАЖ: {target_calories} ккал/день

{today_nutrition}

На основі того, що користувач з'їв СЬОГОДНІ, дай конкретні рекомендації:

1. 📊 АНАЛІЗ СЬОГОДНІШНЬОГО ХАРЧУВАННЯ:
   - Чи достатньо калорій на сьогодні?
   - Баланс білків/жирів/вуглеводів
   - Що добре в сьогоднішньому раціоні?

2. 🎯 ЩО РОБИТИ ДАЛІ СЬОГОДНІ:
   - Чи потрібно ще щось з'їсти сьогодні?
   - Конкретні страви/продукти на вечерю
   - Скільки ще калорій можна/треба з'їсти

3. 💡 ПОРАДИ НА ЗАВТРА:
   - Що покращити в завтрашньому харчуванні
   - Конкретні продукти

Будь конкретним та практичним. Враховуй українську кухню. Відповідай українською."""
                else:
                    prompt = f"""You are a professional nutritionist. Analyze what the user ate TODAY and provide personalized recommendations.

TARGET CALORIES: {target_calories} kcal/day

{today_nutrition}

Based on what the user ate TODAY, provide specific recommendations:

1. 📊 TODAY'S NUTRITION ANALYSIS:
   - Are there enough calories for today?
   - Protein/fat/carb balance
   - What's good about today's diet?

2. 🎯 WHAT TO DO NEXT TODAY:
   - Should they eat something else today?
   - Specific meals/foods for dinner
   - How many more calories can/should they eat

3. 💡 ADVICE FOR TOMORROW:
   - What to improve in tomorrow's nutrition
   - Specific products

Be specific and practical. Respond in English."""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800
                )

                return response.choices[0].message.content.strip()
            else:
                if lang == "uk":
                    return f"""💡 **Базові рекомендації:**

🎯 **Ваша денна норма:** {enhanced_profile.get('calories', {}).get('maintain', 2000)} ккал

📝 **Сьогодні ви ще нічого не їли.**

Рекомендую почати день з:
• Збалансованого сніданку (300-400 ккал)
• Додайте білки та складні вуглеводи
• Не забувайте про воду

Додайте перші страви через Аналітика, і я дам персональні рекомендації на основі вашого фактичного харчування!"""
                else:
                    return f"""💡 **Basic recommendations:**

🎯 **Your daily target:** {enhanced_profile.get('calories', {}).get('maintain', 2000)} kcal

📝 **You haven't eaten anything today yet.**

I recommend starting the day with:
• Balanced breakfast (300-400 kcal)
• Add proteins and complex carbs
• Don't forget about water

Add your first meals through Analyst, and I'll give personalized recommendations based on your actual nutrition!"""

        except Exception as e:
            return get_nutrition_advice(enhanced_profile, lang)

    async def show_profile(self, user_id: int, lang: str):
        profile = load_user_profile(user_id)
        if not profile:
            return {"status": "no_profile"}

        return {"status": "success", "profile": profile}

    async def handle_message(self, message: AgentMessage):
        msg_type = message.content.get("type")
        data = message.content.get("data", {})

        if msg_type == "meal_added":
            await self._process_new_meal(data)
        elif msg_type == "high_calorie_alert":
            await self._handle_high_calorie_alert(data)
        elif msg_type == "analyze_day":
            await self._analyze_daily_intake(data)
        elif msg_type == "meal_deleted":
            await self._process_meal_deletion(data)

    async def _process_new_meal(self, data: Dict):
        user_id = data["user_id"]
        analysis = data["analysis"]

        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {"meal_count": 0, "last_meals": []}

        self.user_profiles[user_id]["meal_count"] += 1
        self.user_profiles[user_id]["last_meals"].append({
            "kbju": data["kbju"],
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })

    async def _handle_high_calorie_alert(self, data: Dict):
        user_id = data["user_id"]
        calories = data["calories"]

        if user_id not in self.alerts:
            self.alerts[user_id] = []

        self.alerts[user_id].append({
            "type": "high_calorie",
            "calories": calories,
            "meal": data["meal"],
            "timestamp": datetime.now().isoformat()
        })

    async def _analyze_daily_intake(self, data: Dict):
        user_id = data["user_id"]
        total_calories = data["total_calories"]

        if total_calories > 2500:
            recommendation = "Recommend reducing portions tomorrow"
        elif total_calories < 1200:
            recommendation = "Too few calories, add a snack"
        else:
            recommendation = "Good calorie balance"

    async def _process_meal_deletion(self, data: Dict):
        user_id = data["user_id"]

        if user_id in self.user_profiles:
            if "meal_count" in self.user_profiles[user_id]:
                self.user_profiles[user_id]["meal_count"] -= 1


# ============================================================================
# Coordinator
# ============================================================================

class SimpleCoordinator:
    def __init__(self):
        self.message_bus = SimpleMessageBus()
        self.agents = {
            "analyst": AnalystAgent(self.message_bus),
            "dietitian": DietitianAgent(self.message_bus)
        }
        self.user_languages = {}
        self.user_states = {}

    async def route_request(self, user_id: int, action: str, data: Dict):
        await self._process_agent_messages()

        if action in ["add_meal", "daily_summary", "delete_meal", "confirm_delete"]:
            if action == "add_meal":
                return await self.agents["analyst"].add_meal(user_id, data["meal_desc"], data["lang"])
            elif action == "daily_summary":
                return await self.agents["analyst"].get_daily_summary(user_id, data["lang"])
            elif action == "delete_meal":
                return await self.agents["analyst"].delete_meal(user_id, data["lang"])
            elif action == "confirm_delete":
                return await self.agents["analyst"].confirm_delete_meal(user_id, data["index"], data["lang"])

        elif action in ["calculate_calories", "get_recommendations", "show_profile"]:
            if action == "calculate_calories":
                return await self.agents["dietitian"].calculate_calories(user_id, data["user_data"])
            elif action == "get_recommendations":
                return await self.agents["dietitian"].get_recommendations(user_id, data["lang"])
            elif action == "show_profile":
                return await self.agents["dietitian"].show_profile(user_id, data["lang"])

        return {"status": "unknown_action"}

    async def _process_agent_messages(self):
        for agent in self.agents.values():
            await agent.process_messages()
