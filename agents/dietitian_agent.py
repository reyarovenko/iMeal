import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def calculate_daily_calories(age: int, gender: str, weight: float, height: int, activity_coefficient: float) -> dict:
    """
    Calculate daily calorie requirement using Mifflin-St Jeor formula
    """
    # Basal Metabolic Rate (BMR)
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # female
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Total calorie expenditure considering activity
    total_calories = bmr * activity_coefficient

    return {
        "bmr": round(bmr),
        "total": round(total_calories),
        "maintain": round(total_calories),
        "lose": round(total_calories - 300),  # 300 kcal deficit for weight loss
        "gain": round(total_calories + 300)  # 300 kcal surplus for weight gain
    }


def get_nutrition_advice(user_profile: dict, lang: str = "uk") -> str:
    """
    Get personalized nutrition recommendations through GPT
    """
    if lang == "uk":
        prompt = f"""
Ти - професійний дієтолог. На основі даних клієнта дай персональні рекомендації щодо харчування.

Дані клієнта:
- Вік: {user_profile['age']} років
- Стать: {"чоловік" if user_profile['gender'] == 'male' else "жінка"}
- Вага: {user_profile['weight']} кг
- Зріст: {user_profile['height']} см
- Калорії для підтримання ваги: {user_profile['calories']['maintain']} ккал/день
- Калорії для схуднення: {user_profile['calories']['lose']} ккал/день
- Калорії для набору ваги: {user_profile['calories']['gain']} ккал/день

Дай конкретні рекомендації:
1. Оптимальний розподіл БЖУ (білки/жири/вуглеводи)
2. Рекомендації щодо режиму харчування
3. Корисні продукти для цієї людини
4. Що варто обмежити або уникати
5. Поради щодо питного режиму

Відповідай українською, будь конкретним та практичним.
        """
    else:
        prompt = f"""
You are a professional nutritionist. Based on client data, provide personalized nutrition recommendations.

Client data:
- Age: {user_profile['age']} years
- Gender: {user_profile['gender']}
- Weight: {user_profile['weight']} kg
- Height: {user_profile['height']} cm
- Calories to maintain weight: {user_profile['calories']['maintain']} kcal/day
- Calories to lose weight: {user_profile['calories']['lose']} kcal/day
- Calories to gain weight: {user_profile['calories']['gain']} kcal/day

Provide specific recommendations:
1. Optimal macronutrient distribution (protein/fat/carbohydrates)
2. Meal timing recommendations
3. Beneficial foods for this person
4. What to limit or avoid
5. Hydration advice

Be specific and practical in your response.
        """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )

    return response.choices[0].message.content.strip()


def analyze_meal_for_goals(meal_description: str, user_profile: dict, lang: str = "uk") -> str:
    """
    Analyze meal in relation to user's goals
    """
    target_calories = user_profile['calories']['maintain']

    if lang == "uk":
        prompt = f"""
Ти - дієтолог. Проаналізуй цей прийом їжі для клієнта з такими параметрами:
- Денна норма калорій: {target_calories} ккал
- Вік: {user_profile['age']} років
- Стать: {"чоловік" if user_profile['gender'] == 'male' else "жінка"}

Прийом їжі: {meal_description}

Дай короткий аналіз:
1. Чи підходить цей прийом їжі для цілей клієнта?
2. Що добре в цьому прийомі їжі?
3. Що можна покращити?
4. Короткі рекомендації

Відповідай коротко та конкретно.
        """
    else:
        prompt = f"""
You are a nutritionist. Analyze this meal for a client with these parameters:
- Daily calorie target: {target_calories} kcal
- Age: {user_profile['age']} years
- Gender: {user_profile['gender']}

Meal: {meal_description}

Provide a brief analysis:
1. Is this meal suitable for the client's goals?
2. What's good about this meal?
3. What could be improved?
4. Brief recommendations

Be concise and specific.
        """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400
    )

    return response.choices[0].message.content.strip()


def get_meal_suggestions(user_profile: dict, meal_type: str, lang: str = "uk") -> str:
    """
    Get meal suggestions for specific meal type
    """
    target_calories = user_profile['calories']['maintain']

    # Approximate calorie distribution by meals
    meal_calories = {
        "breakfast": int(target_calories * 0.25),  # 25% for breakfast
        "lunch": int(target_calories * 0.35),  # 35% for lunch
        "dinner": int(target_calories * 0.30),  # 30% for dinner
        "snack": int(target_calories * 0.10)  # 10% for snack
    }

    calories_for_meal = meal_calories.get(meal_type.lower(), int(target_calories * 0.25))

    if lang == "uk":
        meal_names = {
            "breakfast": "сніданок",
            "lunch": "обід",
            "dinner": "вечеря",
            "snack": "перекус"
        }
        meal_name = meal_names.get(meal_type.lower(), "прийом їжі")

        prompt = f"""
Ти - дієтолог. Запропонуй 3 варіанти здорових страв для {meal_name} для клієнта:
- Денна норма: {target_calories} ккал
- На цей {meal_name}: приблизно {calories_for_meal} ккал
- Вік: {user_profile['age']} років
- Стать: {"чоловік" if user_profile['gender'] == 'male' else "жінка"}

Дай 3 конкретні варіанти з:
- Назвою страви
- Орієнтовною калорійністю
- Коротким описом користі

Формат: емодзі + назва + калорії + опис
        """
    else:
        prompt = f"""
You are a nutritionist. Suggest 3 healthy meal options for {meal_type} for a client:
- Daily target: {target_calories} kcal
- For this {meal_type}: approximately {calories_for_meal} kcal
- Age: {user_profile['age']} years
- Gender: {user_profile['gender']}

Provide 3 specific options with:
- Meal name
- Approximate calories
- Brief benefit description

Format: emoji + name + calories + description
        """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=600
    )

    return response.choices[0].message.content.strip()


def load_user_profile(user_id: int) -> dict:
    """Load user profile"""
    profile_file = "data/profiles.json"

    try:
        with open(profile_file, "r", encoding="utf-8") as f:
            profiles = json.load(f)
        return profiles.get(str(user_id))
    except FileNotFoundError:
        return None


def calculate_bmi(weight: float, height: int) -> dict:
    """Calculate BMI and category"""
    height_m = height / 100
    bmi = weight / (height_m ** 2)

    if bmi < 18.5:
        category_uk = "Недостатня вага"
        category_en = "Underweight"
        recommendation_uk = "Рекомендується набір ваги"
        recommendation_en = "Weight gain recommended"
    elif 18.5 <= bmi < 25:
        category_uk = "Нормальна вага"
        category_en = "Normal weight"
        recommendation_uk = "Підтримуйте поточну вагу"
        recommendation_en = "Maintain current weight"
    elif 25 <= bmi < 30:
        category_uk = "Надмірна вага"
        category_en = "Overweight"
        recommendation_uk = "Рекомендується зниження ваги"
        recommendation_en = "Weight loss recommended"
    else:
        category_uk = "Ожиріння"
        category_en = "Obesity"
        recommendation_uk = "Обов'язково зверніться до лікаря"
        recommendation_en = "Consult a doctor immediately"

    return {
        "bmi": round(bmi, 1),
        "category_uk": category_uk,
        "category_en": category_en,
        "recommendation_uk": recommendation_uk,
        "recommendation_en": recommendation_en
    }
