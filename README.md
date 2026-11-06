# 🥗 Meal Prep Plan

An AI meal-prep assistant built with [Google ADK](https://google.github.io/adk-docs/) and Gemini.
It looks at what's in your pantry, your nutrition goals, and your Google Calendar, then suggests
meals and books cooking time on your calendar — **but only after you approve the plan**.

## What it can do

- 📅 **Plan your week** – suggests meals and finds free time slots in your calendar
- 🥚 **Use what you have** – only suggests recipes that use ingredients in your pantry
- 🎯 **Respect your goals** – aims for your calorie, protein, and fiber targets and never suggests foods you avoid
- 📖 **Show recipes** – full ingredients, equipment, and step-by-step instructions
- ✏️ **Adapt recipes** – e.g. "make it lower calorie with egg whites"
- ⏰ **Book cooking time** – adds events with the recipe steps and a reminder to your Google Calendar

## Example conversation

> **You:** Plan my meal prep for this weekend.
>
> **Agent:** Here's a plan: Saturday 9:00–9:15 Cheesy Spinach Omelette, Saturday 12:30–13:00 Spicy Tofu & Broccoli Rice Bowl… Shall I book these?
>
> **You:** Yes, book them.
>
> **Agent:** Done! 3 events added to your calendar.

## Project structure

```
meal-prep-project/
├── meal_prep/
│   ├── agent.py            # The agent and its tools (pantry, goals, recipes, date)
│   ├── calendar_client.py  # Google Calendar: read busy times, book events
│   ├── recipes.json        # Recipe list
│   ├── goals.json          # Your nutrition targets and food preferences
│   └── .env.example        # Template for your API key
└── requirements.txt
```

## Setup

### 1. Install

You need Python 3.10 or newer.

```bash
git clone https://github.com/PankyThakur/Meal-Prep-Plan.git
cd Meal-Prep-Plan
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Add your Gemini API key

Get a free key from [Google AI Studio](https://aistudio.google.com/apikey), then:

```bash
cp meal_prep/.env.example meal_prep/.env
```

Open `meal_prep/.env` and paste your key into `GOOGLE_API_KEY`.

### 3. Connect Google Calendar

1. In the [Google Cloud Console](https://console.cloud.google.com/), create a project and enable the **Google Calendar API**.
2. Create an **OAuth client ID** of type **Desktop app** and download it.
3. Rename the file to `credentials.json` and put it in the project root (next to `requirements.txt`).
4. Open [meal_prep/calendar_client.py](meal_prep/calendar_client.py) and set `CALENDAR_ID` to your calendar's ID
   (Google Calendar → Settings → your calendar → *Integrate calendar*). Use `"primary"` for your main calendar.

The first time the agent touches your calendar, a browser window opens so you can sign in.
After that, a `token.json` is saved so you don't need to sign in again.

### 4. Run it

From the project root:

```bash
adk web
```

Open the link it prints (usually http://localhost:8000), choose **meal_prep**, and start chatting.
Prefer the terminal? Use `adk run meal_prep` instead.

## Make it yours

| What | Where |
|------|-------|
| Your pantry items | `get_pantry()` in [meal_prep/agent.py](meal_prep/agent.py) |
| Calorie/protein/fiber targets, diet, dislikes, favorites | [meal_prep/goals.json](meal_prep/goals.json) |
| Recipes | [meal_prep/recipes.json](meal_prep/recipes.json) |
| Time zone (default `America/New_York`) | [agent.py](meal_prep/agent.py) and [calendar_client.py](meal_prep/calendar_client.py) |

## 🔒 Keep these files private

These are listed in `.gitignore` and must never be committed:

- `meal_prep/.env` – your Gemini API key
- `credentials.json` – your Google OAuth client
- `token.json` – your Google sign-in token

## Notes

- Calorie and protein numbers are rough estimates, not medical advice.
- The agent never books anything until you explicitly say yes to the plan.
