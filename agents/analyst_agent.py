# agents/analyst_agent.py

import json
import os
import re
from datetime import datetime, date
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def estimate_kbju(food_description: str, lang: str = "uk") -> dict:
    """
    Estimate KBJU (calories, proteins, fats, carbohydrates) for food description using GPT
    """
    if lang == "uk":
        prompt = f"""
Ти - професійний дієтолог та експерт з підрахунку калорій. Проаналізуй цей опис їжі та дай точну оцінку КБЖУ.

Опис їжі: {food_description}

ВАЖЛИВО:
- Враховуй спосіб приготування (варена, смажена, сира тощо)
- Враховуй вказані ваги продуктів
- Якщо вага не вказана, використовуй стандартні порції
- Будь максимально точним в розрахунках

Дай відповідь ТІЛЬКИ в форматі JSON:
{{
    "calories": число,
    "protein": число,
    "fat": число,
    "carbs": число,
    "analysis": "короткий коментар українською"
}}

Числа мають бути цілими.
        """
    else:
        prompt = f"""
You are a professional nutritionist and calorie counting expert. Analyze this food description and provide accurate KBJU estimation.

Food description: {food_description}

IMPORTANT:
- Consider cooking method (boiled, fried, raw, etc.)
- Consider specified weights of products
- If weight not specified, use standard portions
- Be as accurate as possible in calculations

Respond ONLY in JSON format:
{{
    "calories": number,
    "protein": number,
    "fat": number,
    "carbs": number,
    "analysis": "brief comment in English"
}}

Numbers should be integers.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise nutrition calculator. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Low temperature for more accurate calculations
            max_tokens=300
        )

        response_text = response.choices[0].message.content.strip()

        # Attempt to extract JSON from response
        try:
            # Search for JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                kbju_data = json.loads(json_str)

                # Check and validate data
                required_keys = ['calories', 'protein', 'fat', 'carbs']
                for key in required_keys:
                    if key not in kbju_data:
                        raise ValueError(f"Missing key: {key}")
                    # Convert to integers
                    kbju_data[key] = int(float(kbju_data[key]))

                # Add analysis if missing
                if 'analysis' not in kbju_data:
                    kbju_data['analysis'] = "Розрахунок виконано" if lang == "uk" else "Calculation completed"

                return kbju_data
            else:
                raise ValueError("No JSON found in response")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing GPT response: {e}")
            print(f"GPT response: {response_text}")

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")



def analyze_daily_nutrition(entries: list, target_calories: int = None, lang: str = "uk") -> str:
    """
    Analyze daily nutrition intake using GPT
    """
    if not entries:
        return "Немає даних для аналізу" if lang == "uk" else "No data to analyze"

    # Calculate total indicators
    total_calories = sum(entry.get('calories', 0) for entry in entries)
    total_protein = sum(entry.get('protein', 0) for entry in entries)
    total_fat = sum(entry.get('fat', 0) for entry in entries)
    total_carbs = sum(entry.get('carbs', 0) for entry in entries)

    # Prepare meals list
    meals_list = []
    for entry in entries:
        meal_desc = entry.get('description', 'Невідома страва')
        calories = entry.get('calories', 0)
        protein = entry.get('protein', 0)
        fat = entry.get('fat', 0)
        carbs = entry.get('carbs', 0)
        meals_list.append(f"- {meal_desc} ({calories} ккал, {protein}г білка, {fat}г жирів, {carbs}г вуглеводів)")

    meals_text = "\n".join(meals_list)

    if lang == "uk":
        target_info = f"\n- Цільові калорії: {target_calories} ккал" if target_calories else ""

        prompt = f"""
Ти - професійний дієтолог. Проаналізуй денний раціон харчування клієнта.

СТРАВИ ЗА ДЕНЬ:
{meals_text}

ЗАГАЛЬНІ ПОКАЗНИКИ:
- Загальні калорії: {total_calories} ккал
- Білки: {total_protein} г
- Жири: {total_fat} г
- Вуглеводи: {total_carbs} г{target_info}

Дай детальний аналіз:

🎯 **Загальна оцінка раціону:**
(оцінка збалансованості та калорійності)

✅ **Позитивні моменти:**
(що добре в цьому раціоні)

⚠️ **Що потребує уваги:**
(недоліки або занепокоєння)

💡 **Рекомендації:**
(конкретні поради для покращення)

🍎 **Що додати завтра:**
(конкретні продукти або страви)

Будь конкретним та практичним. Використовуй емодзі для структури.
        """
    else:
        target_info = f"\n- Target calories: {target_calories} kcal" if target_calories else ""

        prompt = f"""
You are a professional nutritionist. Analyze the daily nutrition intake of a client.

MEALS FOR THE DAY:
{meals_text}

TOTAL INDICATORS:
- Total calories: {total_calories} kcal
- Protein: {total_protein} g
- Fat: {total_fat} g
- Carbohydrates: {total_carbs} g{target_info}

Provide detailed analysis:

🎯 **Overall diet assessment:**
(evaluation of balance and caloric intake)

✅ **Positive aspects:**
(what's good about this diet)

⚠️ **Areas of concern:**
(deficiencies or concerns)

💡 **Recommendations:**
(specific advice for improvement)

🍎 **What to add tomorrow:**
(specific foods or meals)

Be specific and practical. Use emojis for structure.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional nutritionist providing detailed, practical advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=800
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error analyzing nutrition: {e}")
        if lang == "uk":
            return f"""
📊 **Загальна статистика за день:**
• Калорії: {total_calories} ккал
• Білки: {total_protein} г
• Жири: {total_fat} г  
• Вуглеводи: {total_carbs} г

❌ Помилка при отриманні детального аналізу від ШІ.
            """
        else:
            return f"""
📊 **Daily statistics:**
• Calories: {total_calories} kcal
• Protein: {total_protein} g
• Fat: {total_fat} g
• Carbohydrates: {total_carbs} g

❌ Error getting detailed AI analysis.
            """


def analyze_meal_for_goals(meal_description: str, meal_kbju: dict, target_calories: int = None,
                           lang: str = "uk") -> str:
    """
    Analyze individual meal in relation to goals
    """
    calories = meal_kbju.get('calories', 0)
    protein = meal_kbju.get('protein', 0)
    fat = meal_kbju.get('fat', 0)
    carbs = meal_kbju.get('carbs', 0)

    if lang == "uk":
        target_info = f"\nДенна норма калорій: {target_calories} ккал" if target_calories else ""

        prompt = f"""
Ти - дієтолог. Проаналізуй цей прийом їжі:

Страва: {meal_description}
Калорії: {calories} ккал
Білки: {protein} г
Жири: {fat} г
Вуглеводи: {carbs} г{target_info}

Дай короткий аналіз (до 200 слів):
1. Чи підходить для здорового харчування?
2. Що добре в цій страві?
3. Що можна покращити?
4. Короткі рекомендації

Відповідай коротко та конкретно українською.
        """
    else:
        target_info = f"\nDaily calorie target: {target_calories} kcal" if target_calories else ""

        prompt = f"""
You are a nutritionist. Analyze this meal:

Meal: {meal_description}
Calories: {calories} kcal
Protein: {protein} g
Fat: {fat} g
Carbohydrates: {carbs} g{target_info}

Provide brief analysis (up to 200 words):
1. Is it suitable for healthy eating?
2. What's good about this meal?
3. What could be improved?
4. Brief recommendations

Be concise and specific.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutritionist providing concise meal analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error analyzing meal: {e}")
        if lang == "uk":
            return f"Страва: {calories} ккал. Помилка аналізу ШІ."
        else:
            return f"Meal: {calories} kcal. AI analysis error."


def is_meal_description(text: str) -> bool:
    """
    Check if text is a food description
    """
    # Simple check - if there are letters and it's not a command
    return bool(re.search(r'[а-яёa-z]', text.lower())) and not text.startswith('/')


def get_weekly_nutrition_summary(entries_by_date: dict, lang: str = "uk") -> str:
    """
    Weekly nutrition analysis using GPT
    """
    if not entries_by_date:
        return "Немає даних за тиждень" if lang == "uk" else "No weekly data"

    # Prepare daily data
    daily_summaries = []
    total_week_calories = 0
    total_week_protein = 0
    total_week_fat = 0
    total_week_carbs = 0

    for date_str, entries in entries_by_date.items():
        day_calories = sum(entry.get('calories', 0) for entry in entries)
        day_protein = sum(entry.get('protein', 0) for entry in entries)
        day_fat = sum(entry.get('fat', 0) for entry in entries)
        day_carbs = sum(entry.get('carbs', 0) for entry in entries)

        total_week_calories += day_calories
        total_week_protein += day_protein
        total_week_fat += day_fat
        total_week_carbs += day_carbs

        daily_summaries.append(f"{date_str}: {day_calories} ккал, {len(entries)} прийомів")

    avg_daily_calories = total_week_calories // len(entries_by_date) if entries_by_date else 0

    days_text = "\n".join(daily_summaries)

    if lang == "uk":
        prompt = f"""
Ти - дієтолог. Проаналізуй тижневий раціон харчування клієнта.

ДАНІ ПО ДНЯХ:
{days_text}

ЗАГАЛЬНА СТАТИСТИКА ТИЖНЯ:
- Загальні калорії за тиждень: {total_week_calories} ккал
- Середньодобові калорії: {avg_daily_calories} ккал
- Загальні білки: {total_week_protein} г
- Загальні жири: {total_week_fat} г
- Загальні вуглеводи: {total_week_carbs} г
- Кількість днів з даними: {len(entries_by_date)}

Дай аналіз:
📈 **Тижневі тенденції**
🎯 **Постійність харчування**
💡 **Рекомендації на наступний тиждень**

Будь конкретним та практичним.
        """
    else:
        prompt = f"""
You are a nutritionist. Analyze the weekly nutrition intake of a client.

DAILY DATA:
{days_text}

WEEKLY STATISTICS:
- Total weekly calories: {total_week_calories} kcal
- Average daily calories: {avg_daily_calories} kcal
- Total protein: {total_week_protein} g
- Total fat: {total_week_fat} g
- Total carbohydrates: {total_week_carbs} g
- Days with data: {len(entries_by_date)}

Provide analysis:
📈 **Weekly trends**
🎯 **Consistency of nutrition**
💡 **Recommendations for next week**

Be specific and practical.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutritionist providing weekly nutrition analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=600
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error analyzing weekly nutrition: {e}")
        if lang == "uk":
            return f"""
📊 **Тижнева статистика:**
• Середньодобові калорії: {avg_daily_calories} ккал
• Днів з даними: {len(entries_by_date)}
• Загальні калорії: {total_week_calories} ккал

❌ Помилка при отриманні детального аналізу.
            """
        else:
            return f"""
📊 **Weekly statistics:**
• Average daily calories: {avg_daily_calories} kcal
• Days with data: {len(entries_by_date)}
• Total calories: {total_week_calories} kcal

❌ Error getting detailed analysis.
            """
