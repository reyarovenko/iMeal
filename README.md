# Nutrition Tracker Bot

A multi-agent Telegram bot for tracking daily nutrition and getting personalized dietary recommendations. The bot uses AI to analyze food intake and provide Calories, Proteins, Fats, Carbohydrates calculations.

##  Features

- **Food Analysis**: AI-powered food recognition and nutritional analysis
- **Daily Tracking**: Track your daily meals with detailed CPFC breakdown
- **Calorie Calculator**: Calculate your daily calorie needs based on personal data
- **Smart Recommendations**: Get personalized nutrition advice based on your eating patterns
- **Easy Management**: Add and delete meals with intuitive button interface
- **Multi-language**: Supports Ukrainian and English
- **Multi-agent System**: Two specialized AI agents working together

## Architecture

The bot uses a multi-agent architecture with two specialized agents:

- **Analyst Agent**: Handles food analysis, KBJU calculations, and daily summaries
- **Dietitian Agent**: Provides recommendations, calorie calculations, and user profiles

## Quick Start

### Prerequisites

- Python 3.8+
- Telegram Bot Token
- OpenAI API Key

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd nutrition-tracker-bot
```

2. **Install dependencies:**
```bash
pip install python-telegram-bot python-dotenv openai
```

3. **Set up environment variables:**
Create a `.env` file in the project root:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

4. **Run the bot:**
```bash
python main.py
```

## 📁 Project Structure

```
nutrition-tracker-bot/
├── main.py                   # Main bot file with Telegram handlers
├── multiagent_core.py        # Multi-agent system coordinator
├── agents/
│   ├── analyst_agent.py      # Food analysis and tracking agent
│   └── dietitian_agent.py    # Nutrition recommendations agent
├── data/                     # Auto-created data storage
│   ├── nutrition_data.json   # Daily food entries
│   └── profiles.json         # User profiles and calorie data
├── .env                      # Environment variables (create this)
└── README.md                 # This file
```

## How to Use

1. **Start the bot:** Send `/start` to your bot
2. **Choose language:** Select Ukrainian 🇺🇦 or English 🇬🇧
3. **Main features:**
   - **Analyst** - Track your meals and view daily summaries
   - **Dietitian** - Calculate calories and get recommendations

### Adding Food
1. Go to Analyst → Add Food
2. Select meal type (Breakfast, Lunch, Dinner, Snack)
3. Describe what you ate (e.g., "2 eggs, 1 slice of bread")
4. Get instant calories and macros analysis

### Getting Recommendations
1. First, calculate your daily calories in Dietitian section
2. Add some meals through Analyst
3. Go to Dietitian → Recommendations for personalized advice

## Configuration

### Without OpenAI API
The bot works with basic functionality:
- Manual calories and macros calculations using formulas
- Basic nutrition recommendations

### With OpenAI API
Enhanced features:
- AI-powered food recognition
- Detailed nutritional analysis
- Personalized recommendations based on actual intake

## Data Storage

- **User data**: Stored locally in JSON files
- **Daily nutrition**: `data/nutrition_data.json`
- **User profiles**: `data/profiles.json`
- **No external database required**

## Key Features Explained

### Multi-Agent Communication
- Agents communicate through a message bus system
- Analyst notifies Dietitian about high-calorie meals
- Dietitian requests nutrition data for personalized advice

### Smart Button Interface
- Intuitive button-based navigation
- Dynamic deletion menu with meal-specific buttons
- No need to remember numbers or commands


##  Future Enhancements

-  Photo recognition for food items
-  Weekly/monthly nutrition reports
-  Goal setting and progress tracking
