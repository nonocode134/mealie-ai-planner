import requests
from datetime import date, timedelta


class MealieClient:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get(self, path, params=None):
        resp = requests.get(f"{self.base_url}{path}", headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path, data):
        resp = requests.post(f"{self.base_url}{path}", headers=self.headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path):
        resp = requests.delete(f"{self.base_url}{path}", headers=self.headers, timeout=30)
        resp.raise_for_status()

    def get_all_recipes(self):
        data = self._get("/api/recipes", params={"perPage": 9999, "page": 1})
        items = data.get("items", [])
        return [
            {
                "id": r.get("id"),
                "slug": r.get("slug"),
                "name": r.get("name"),
                "tags": [t.get("name") for t in (r.get("tags") or [])],
                "categories": [c.get("name") for c in (r.get("recipeCategory") or [])],
            }
            for r in items
        ]

    def get_recipe_by_slug(self, slug):
        return self._get(f"/api/recipes/{slug}")

    def get_meal_plans_in_range(self, start_date, end_date):
        data = self._get(
            "/api/households/mealplans",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "perPage": 9999,
                "page": 1,
            },
        )
        return data.get("items", [])

    def create_meal_plan(self, plan_date, recipe_id, entry_type):
        return self._post(
            "/api/households/mealplans",
            {"date": plan_date, "entryType": entry_type, "recipeId": recipe_id},
        )

    def delete_meal_plan(self, plan_id):
        self._delete(f"/api/households/mealplans/{plan_id}")
