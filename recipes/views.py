import uuid

from django.conf import settings
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from dotenv import dotenv_values
from google import genai

from .catalog import CATEGORIES, PRODUCTS, build_products
from .models import SavedRecipe


ALLOWED_LANGUAGES = {"kk", "ru"}
ALLOWED_MINUTES = {"15", "30", "60"}


def index(request):
    language = "kk"
    products = ""
    minutes = "30"
    vegetarian = False
    recipe = ""
    error = ""
    can_save = False
    selected_products = []

    if request.method == "POST":
        posted_language = (request.POST.get("language") or "").strip()
        language = (
            posted_language
            if posted_language in ALLOWED_LANGUAGES
            else "kk"
        )

        products = request.POST.get("products", "")

        posted_minutes = (request.POST.get("minutes") or "").strip()
        minutes = (
            posted_minutes
            if posted_minutes in ALLOWED_MINUTES
            else "30"
        )

        vegetarian = request.POST.get("vegetarian") == "1"

        raw_ids = request.POST.getlist("selected_products")
        selected_products = list(dict.fromkeys(raw_ids))

        action = (request.POST.get("action") or "").strip()

        if action in {"language", "generate"}:
            request.session.pop("smartchef_draft", None)

        if action == "language":
            recipe = ""

        elif action == "generate":
            try:
                selected_products, combined_products = build_products(
                    selected_products,
                    products,
                    language,
                )

            except ValueError as exc:
                recipe = ""
                can_save = False
                error = str(exc)

            else:
                config = dotenv_values(settings.BASE_DIR / ".env")
                api_key = (config.get("GEMINI_API_KEY") or "").strip()
                model = (
                    (config.get("GEMINI_MODEL") or "").strip()
                    or "gemini-3.8-flash"
                )

                if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
                    if language == "ru":
                        error = "Введите ключ Gemini в файл .env."
                    else:
                        error = ".env файлына Gemini кілтін енгізіңіз."

                else:
                    if language == "ru":
                        vegetarian_text = (
                            "Рецепт должен быть вегетарианским."
                            if vegetarian
                            else "Вегетарианское ограничение не требуется."
                        )

                        prompt = f"""
Составь ровно один рецепт на основе следующих продуктов:
{combined_products}

Ограничение по времени приготовления: {minutes} минут.
{vegetarian_text}

Язык ответа: русский.

Ответ должен содержать только один рецепт со следующей структурой:
1. Название блюда
2. Время приготовления
3. Ингредиенты
4. Нумерованные пошаговые инструкции
5. Совет

Не предлагай несколько вариантов и не добавляй второй рецепт.
""".strip()

                    else:
                        vegetarian_text = (
                            "Рецепт міндетті түрде вегетариандық болсын."
                            if vegetarian
                            else "Вегетариандық шектеу қажет емес."
                        )

                        prompt = f"""
Келесі өнімдер негізінде дәл бір рецепт құрастыр:
{combined_products}

Дайындау уақыты: {minutes} минут.
{vegetarian_text}

Жауап тілі: қазақ тілі.

Жауап тек бір рецепттен тұруы керек және мына құрылымды сақтасын:
1. Тағам атауы
2. Дайындау уақыты
3. Ингредиенттер
4. Нөмірленген дайындау қадамдары
5. Кеңес

Бірнеше нұсқа ұсынба және екінші рецепт қоспа.
""".strip()

                    try:
                        client = genai.Client(api_key=api_key)

                        interaction = client.interactions.create(
                            model=model,
                            input=prompt,
                        )

                        generated_recipe = interaction.output_text

                        if (
                            generated_recipe is None
                            or not generated_recipe.strip()
                        ):
                            recipe = ""
                            can_save = False

                            if language == "ru":
                                error = (
                                    "Не удалось получить рецепт. "
                                    "Попробуйте ещё раз."
                                )
                            else:
                                error = (
                                    "Рецептті алу мүмкін болмады. "
                                    "Қайтадан көріңіз."
                                )

                        else:
                            recipe = generated_recipe.strip()

                            draft = {
                                "token": str(uuid.uuid4()),
                                "products": combined_products,
                                "recipe": recipe,
                                "language": language,
                                "minutes": int(minutes),
                                "vegetarian": bool(vegetarian),
                            }

                            request.session["smartchef_draft"] = draft
                            request.session.modified = True
                            can_save = True

                    except Exception:
                        recipe = ""
                        can_save = False

                        if language == "ru":
                            error = (
                                "Не удалось создать рецепт. "
                                "Проверьте настройки Gemini и попробуйте ещё раз."
                            )
                        else:
                            error = (
                                "Рецепт жасау мүмкін болмады. "
                                "Gemini баптауларын тексеріп, "
                                "қайтадан көріңіз."
                            )

        else:
            recipe = ""
            can_save = False

            if language == "ru":
                error = "Не удалось определить действие."
            else:
                error = "Әрекетті анықтау мүмкін болмады."

    catalog_data = {
        "categories": CATEGORIES,
        "products": PRODUCTS,
        "language": language,
    }

    return render(
        request,
        "recipes/index.html",
        {
            "language": language,
            "products": products,
            "minutes": minutes,
            "vegetarian": vegetarian,
            "recipe": recipe,
            "error": error,
            "can_save": can_save,
            "categories": CATEGORIES,
            "catalog_products": PRODUCTS,
            "selected_products": selected_products,
            "catalog_data": catalog_data,
        },
    )


@require_POST
def save_recipe(request):
    draft = request.session.get("smartchef_draft")

    if not draft:
        return redirect("recipes:index")

    SavedRecipe.objects.get_or_create(
        token=draft["token"],
        defaults={
            "products": draft["products"],
            "recipe": draft["recipe"],
            "language": draft["language"],
            "minutes": draft["minutes"],
            "vegetarian": draft["vegetarian"],
        },
    )

    language = draft.get("language", "kk")

    if language not in ALLOWED_LANGUAGES:
        language = "kk"

    return redirect(f"/saved/?language={language}")


def saved_recipes(request):
    posted_language = (request.GET.get("language") or "").strip()

    language = (
        posted_language
        if posted_language in ALLOWED_LANGUAGES
        else "kk"
    )

    saved = SavedRecipe.objects.all()

    return render(
        request,
        "recipes/saved.html",
        {
            "saved_recipes": saved,
            "language": language,
        },
    )