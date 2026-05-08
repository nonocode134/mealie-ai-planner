# Mealie AI Planner — Home Assistant Add-on

Génère automatiquement des menus de repas avec l'IA (OpenAI) en tenant compte des saisons, de votre localisation et des recettes récemment planifiées, puis les écrit directement dans Mealie.

## Installation

### 1. Rendre ce dépôt public sur GitHub

Le dépôt doit être **public** pour que Home Assistant puisse y accéder.

### 2. Ajouter le dépôt dans Home Assistant

1. Allez dans **Paramètres → Add-ons → ··· (menu en haut à droite) → Dépôts**
2. Ajoutez l'URL : `https://github.com/nonocode134/mealie-ai-planner`
3. Cliquez sur **Ajouter**

### 3. Installer l'add-on

1. Dans la liste des add-ons, cherchez **Mealie AI Planner**
2. Cliquez sur **Installer**
3. Attendez la fin du build Docker

### 4. Configurer l'add-on

Dans l'onglet **Configuration** de l'add-on, renseignez :

| Paramètre | Description | Exemple |
|---|---|---|
| `mealie_url` | URL de votre instance Mealie | `http://192.168.1.50:9925` |
| `mealie_token` | Bearer token API Mealie | `eyJ0eXAiOiJK...` |
| `openai_api_key` | Clé API OpenAI | `sk-proj-...` |
| `openai_model` | Modèle OpenAI | `gpt-4o` |
| `location` | Localisation pour la saisonnalité | `Lausanne, Suisse` |
| `default_planning_days` | Nombre de jours à planifier | `7` |
| `weekday_meals` | Types de repas en semaine | `["dinner"]` |
| `weekend_meals` | Types de repas le week-end | `["lunch", "dinner"]` |
| `avoid_repeat_days` | Éviter répétition sous X jours | `14` |

**Obtenir le token Mealie :** dans Mealie → Profil → API Tokens → Créer un token.

### 5. Démarrer et accéder à l'interface

1. Démarrez l'add-on
2. Ouvrez l'onglet **Interface** ou cliquez sur **Ouvrir l'interface web**
3. Sélectionnez la date de départ et le nombre de jours
4. Cliquez sur **🍽️ Générer les menus**

## Automatisation Home Assistant

Déclencher automatiquement la génération chaque mercredi à 15h :

```yaml
rest_command:
  generate_mealie_menu:
    url: "http://localhost:8099/api/generate"
    method: POST
    content_type: "application/json"
    payload: >-
      {"start_date": "{{ (now() + timedelta(days=1)).strftime('%Y-%m-%d') }}",
       "planning_days": 7}

automation:
  - alias: "Générer menus semaine"
    trigger:
      platform: time
      at: "15:00:00"
    condition:
      condition: time
      weekday:
        - wed
    action:
      service: rest_command.generate_mealie_menu
```

## API

| Endpoint | Méthode | Description |
|---|---|---|
| `/` | GET | Interface web |
| `/api/generate` | POST | Déclenche une génération |
| `/api/status` | GET | Dernier résultat |
| `/api/config` | GET | Configuration active (sans secrets) |

Corps du POST `/api/generate` (optionnel) :
```json
{
  "start_date": "2025-05-13",
  "planning_days": 7
}
```

## Notes

- La génération est **idempotente** : elle écrase le planning existant sur la période.
- Les recettes doivent être préalablement importées dans Mealie.
- Les logs sont visibles dans l'onglet **Journal** de l'add-on.
