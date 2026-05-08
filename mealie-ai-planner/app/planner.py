import json
from datetime import date, timedelta
from openai import OpenAI
from mealie import MealieClient


SEASONS = {
    "nord": {
        12: "hiver", 1: "hiver", 2: "hiver",
        3: "printemps", 4: "printemps", 5: "printemps",
        6: "été", 7: "été", 8: "été",
        9: "automne", 10: "automne", 11: "automne",
    }
}


def _get_season(target_date):
    return SEASONS["nord"][target_date.month]


def _build_day_schedule(config, start_date, planning_days):
    weekday_meals = config.get("weekday_meals", ["dinner"])
    weekend_meals = config.get("weekend_meals", ["lunch", "dinner"])
    schedule = []
    for i in range(planning_days):
        d = start_date + timedelta(days=i)
        meal_types = weekend_meals if d.weekday() >= 5 else weekday_meals
        for meal_type in meal_types:
            schedule.append({"date": d.isoformat(), "meal_type": meal_type})
    return schedule


def generate_plan(config, start_date_str, planning_days, custom_instructions=None):
    start_date = date.fromisoformat(start_date_str)
    end_date = start_date + timedelta(days=planning_days - 1)

    client = MealieClient(config["mealie_url"], config["mealie_token"])

    all_recipes = client.get_all_recipes()
    if not all_recipes:
        raise ValueError("Aucune recette trouvée dans Mealie.")

    avoid_days = config.get("avoid_repeat_days", 14)
    recent_start = (start_date - timedelta(days=avoid_days)).isoformat()
    recent_plans = client.get_meal_plans_in_range(recent_start, start_date_str)

    recent_slugs = set()
    for plan in recent_plans:
        recipe = plan.get("recipe")
        if recipe and recipe.get("slug"):
            recent_slugs.add(recipe["slug"])

    slug_to_id = {r["slug"]: r["id"] for r in all_recipes}

    season = _get_season(start_date)
    location = config.get("location", "Lausanne, Suisse")
    schedule = _build_day_schedule(config, start_date, planning_days)

    if custom_instructions is None:
        custom_instructions = config.get("custom_instructions", [])
    instructions_text = "\n".join(f"- {i}" for i in custom_instructions) if custom_instructions else ""

    recipe_list_text = "\n".join(
        f"- {r['name']} (slug: {r['slug']})" + (f" [tags: {', '.join(r['tags'])}]" if r["tags"] else "")
        for r in all_recipes
    )
    recent_text = ", ".join(recent_slugs) if recent_slugs else "aucune"
    schedule_text = "\n".join(
        f"- {s['date']} ({s['meal_type']})" for s in schedule
    )

    system_prompt = (
        "Tu es un assistant culinaire expert en cuisine saisonnière. "
        "Tu génères des plannings de repas équilibrés, variés et adaptés à la saison. "
        "Tu réponds uniquement en JSON valide, sans texte supplémentaire."
    )

    user_prompt = f"""Génère un planning de repas pour les créneaux suivants :

CRÉNEAUX À PLANIFIER :
{schedule_text}

SAISON ET LIEU : {season} à {location}

RECETTES DISPONIBLES DANS MEALIE :
{recipe_list_text}

RECETTES À ÉVITER (vues récemment) : {recent_text}

RÈGLES :
- Utilise uniquement les slugs de la liste ci-dessus
- Ne répète pas les recettes à éviter
- Varie les types de plats (viande, poisson, végétarien...)
- Adapte les recettes à la saison
{instructions_text}

Réponds uniquement avec ce JSON :
{{"meal_plan": [{{"date": "YYYY-MM-DD", "meal_type": "dinner", "recipe_slug": "slug-ici"}}]}}"""

    openai_client = OpenAI(api_key=config["openai_api_key"])
    response = openai_client.chat.completions.create(
        model=config.get("openai_model", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    meal_plan = parsed.get("meal_plan", [])

    existing_plans = client.get_meal_plans_in_range(start_date_str, end_date.isoformat())
    for plan in existing_plans:
        client.delete_meal_plan(plan["id"])

    created = []
    errors = []
    for entry in meal_plan:
        slug = entry.get("recipe_slug")
        meal_type = entry.get("meal_type", "dinner")
        plan_date = entry.get("date")

        recipe_id = slug_to_id.get(slug)
        if not recipe_id:
            try:
                recipe = client.get_recipe_by_slug(slug)
                recipe_id = recipe.get("id")
                slug_to_id[slug] = recipe_id
            except Exception:
                errors.append(f"Slug introuvable : {slug}")
                continue

        try:
            client.create_meal_plan(plan_date, recipe_id, meal_type)
            recipe_name = next((r["name"] for r in all_recipes if r["slug"] == slug), slug)
            created.append({"date": plan_date, "meal_type": meal_type, "recipe": recipe_name, "slug": slug})
        except Exception as e:
            errors.append(f"Erreur création {plan_date} {meal_type} {slug}: {e}")

    return {
        "success": True,
        "start_date": start_date_str,
        "end_date": end_date.isoformat(),
        "planning_days": planning_days,
        "count": len(created),
        "meals": created,
        "errors": errors,
    }
