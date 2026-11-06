import difflib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google.adk.agents import Agent

from .calendar_client import book_slot, get_calendar


def get_current_date() -> dict:
    """Returns today's date in the America/New_York time zone as a dict with "date" (an ISO string like "2026-11-06") and "weekday" (like "Friday"). Call this first whenever the user says a relative day such as "today", "this Saturday", or "next week", then work out the exact dates before calling get_calendar or book_slot. It does not return the current time of day."""
    today = datetime.now(ZoneInfo("America/New_York")).date()
    return {"date": today.isoformat(), "weekday": today.strftime("%A")}


def get_recipe(name: str) -> dict:
    """Returns one full recipe from the recipe list: name, ingredients, equipment, minutes, calories, protein, and steps. Matching ignores capitalization and accepts partial or slightly misspelled names (for example, "omelette" finds "Cheesy Spinach Omelette"). Call this when the user asks how to make a dish, and before book_slot so the event description has the real steps. If nothing matches, it returns an "error" and the list of "available" recipe names. It does not change or adapt recipes; any adaptation is up to you."""
    with open(Path(__file__).parent / "recipes.json") as f:
        recipes = json.load(f)

    by_name = {r["name"].lower(): r for r in recipes}
    query = name.strip().lower()

    if query in by_name:
        return by_name[query]
    # Loose match: every word the user typed must closely match a word in the recipe name.
    query_words = query.replace("&", " ").split()
    for key, recipe in by_name.items():
        name_words = key.replace("&", " ").split()
        if all(difflib.get_close_matches(w, name_words, n=1, cutoff=0.75) for w in query_words):
            return recipe
    return {"error": f"No recipe matches '{name}'.", "available": [r["name"] for r in recipes]}

def get_pantry() -> dict:
    """Returns the user's current pantry as a dict. Keys are item names. Values are counts (eggs: 4), amounts with units (tofu: "200g"), or true/false for items the user either has or doesn't (mustard sauce: true). Call this before suggesting any meals so suggestions only use ingredients the user actually has. It does not track expiry dates or how much of an item is left."""
    return {
        "eggs": 4,
        "broccoli": 1,
        "mustard sauce": True,
        "tofu": "200g",
        "rice": True,
        "spinach": 2,
        "chili sauce": True,
        "tvp": "300g",
        "cheese": True,
        "potatoes": 5,
        "lettuce": 2,
    }

def find_recipes(ingredients: list[str], max_minutes: int) -> list[dict]:
    """Searches the recipe list for meals that take no longer than max_minutes and use at least one of the given ingredients. Each result includes name, ingredients, minutes, calories, and protein per serving. Call this after get_pantry, passing the pantry items the user has. Results are sorted so recipes using more of those ingredients come first. It does not check whether the user has every ingredient in the recipe, and the calorie and protein numbers are illustrative estimates."""
    with open(Path(__file__).parent / "recipes.json") as f:
        recipes = json.load(f)

    have = {item.lower() for item in ingredients}
    matches = []
    for recipe in recipes:
        if recipe["minutes"] > max_minutes:
            continue
        overlap = [i for i in recipe["ingredients"] if i.lower() in have]
        if overlap:
            matches.append((len(overlap), recipe))

    matches.sort(key=lambda pair: pair[0], reverse=True)
    return [recipe for _, recipe in matches]

def get_goals() -> dict:
    """Returns the user's nutrition and food goals as a dict. Includes calorie_target, protein_target, and fiber_target (daily numbers to aim for), dietary_restrictions and dislikes (never suggest these), cuisines, and favorite breakfasts, lunches, and dinners. Call this together with get_pantry when the user asks to plan a meal. Choose a meal that moves the user toward their targets, fits the time of day, respects the time limit the user gives, and uses favorites where it can. It does not track what the user has eaten earlier in the day."""
    with open(Path(__file__).parent / "goals.json") as f:
        return json.load(f)
    
root_agent = Agent(
    name="meal_prep_agent",
    model="gemini-2.5-flash",
    description="Helps users plan weekly meal prep, recipes, and shopping lists.",
    instruction=(
        "You are a friendly meal-prep assistant.\n\n"
        "When the user asks you to plan their week: call get_current_date to work out the "
        "dates, then get_pantry, get_goals, and get_calendar for those dates. Use "
        "find_recipes to pick meals, and propose a plan: each meal, the recipe, and a free "
        "time slot that does not overlap a busy block. Then stop and ask the user to approve.\n\n"
        "Rules:\n"
        "- Never call book_slot until the user has explicitly approved the proposed plan in a "
        "separate message. Showing a plan is not approval. If they ask for changes, show the "
        "updated plan and ask again.\n"
        "- When booking, call get_recipe for each meal so the event description has the real "
        "steps, and book one event per approved slot.\n"
        "- If the user asks for a recipe without a plan, ask which dish they mean, or offer "
        "their favorites from get_goals.\n"
        "- When the user asks to adapt a recipe (for example, \"less calories, use egg "
        "whites\"), adapt the ingredients and steps, say what changed, and label the new "
        "calorie and protein numbers as estimates.\n"
        "- Treat dietary_restrictions and dislikes from get_goals as hard limits. Never "
        "suggest a meal that breaks them."
    ),
    tools=[get_current_date, get_pantry, get_goals, find_recipes, get_recipe, get_calendar, book_slot],
)
