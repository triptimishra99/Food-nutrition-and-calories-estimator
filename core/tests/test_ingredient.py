import pytest

from core.ingredient import Ingredient, IngredientError, IngredientList
from core.models import Food, FoodNutrition, FoodWeight


@pytest.mark.django_db
class TestIngredient:
    def test_sample_water(self):
        nutrients = [
            "ENERC_KCAL",
            "PROCNT",
            "FAT",
            "FASAT",
            "FAPU",
            "FAMS",
            "CHOCDF",
            "SUGAR",
            "CHOLE",
            "NA",
            "K",
            "FIBTG",
        ]
        water = Food.objects.create(name="Water")
        FoodWeight.objects.create(food=water, amount=1, desc="ml", value=1)
        for n in nutrients:
            FoodNutrition.objects.create(
                food=water, desc=n, value=0.0, units="mg", tagname=n
            )
        ing = Ingredient(water.name)
        assert ing.matched_food.id == water.id
        assert ing.energy == 0.0
        assert ing.protein == 0.0
        assert ing.fat == 0.0
        assert ing.fat_sat == 0.0
        assert ing.fat_poly == 0.0
        assert ing.fat_mono == 0.0
        assert ing.carb == 0.0
        assert ing.sugar == 0.0
        assert ing.chol == 0.0
        assert ing.fiber == 0.0
        assert ing.potas == 0.0
        assert ing.sodium == 0.0

    def test_food_with_no_nutrients(self):
        food = Food.objects.create(name="Chicken")
        FoodWeight.objects.create(food=food, amount=1, desc="Pinch", value=1)
        food = Ingredient(food.name)
        assert food.energy is None

    def test_parsing_non_existent_ingredient(self):
        with pytest.raises(IngredientError):
            assert Ingredient("xyz")

    def test_assign_weight(self):
        Food.objects.create(name="Chicken breast")
        ing = Ingredient("1 g of chicken breast")
        assert ing.weight == 1

    def test_raise_when_no_weight(self):
        Food.objects.create(name="Chicken breast")
        with pytest.raises(IngredientError):
            Ingredient(
                "Chicken breast"
            )  # Unit wasn't specified and Chicken doesn't have any weight objects so it should raise IngredientError

    def test_total_nutrition(self):
        food = Food.objects.create(name="Chicken")
        food2 = Food.objects.create(name="Apple")
        FoodNutrition.objects.create(
            food=food,
            desc="Energy (kcal)",
            value=20,
            units="kcal",
            tagname="ENERC_KCAL",
        )
        FoodNutrition.objects.create(
            food=food, desc="Proteins", value=5, units="g", tagname="PROCNT"
        )
        FoodNutrition.objects.create(
            food=food2,
            desc="Energy (kcal)",
            value=10.1,
            units="kcal",
            tagname="ENERC_KCAL",
        )
        ings = IngredientList(["100 g chicken", "100 g apple"])
        total_nutrition = ings.total_nutrition()
        assert total_nutrition["ENERGY"][0] == 30.1
        assert total_nutrition["PROTEIN"][0] == 5
        assert total_nutrition["FAT"][0] == 0.0
        assert total_nutrition["CARB"][0] == 0.0

    def test_serving_nutrition(self):
        chicken = Food.objects.create(name="Chicken")
        FoodNutrition.objects.create(
            food=chicken,
            desc="Energy (kcal)",
            value=20,
            units="kcal",
            tagname="ENERC_KCAL",
        )
        ings = IngredientList(["100 g chicken"])
        serving_nutrition = ings.total_nutrition(2)
        assert (
            serving_nutrition["ENERGY"][1]
            == float(chicken.nutrition.first().value) / 2.0
        )


@pytest.mark.django_db
class TestIngredientList:
    def test_add_to_bad_when_ParseIngredientError(self):
        """Ensure IngredientList handles ParseIngredientError by adding input to bad list"""
        ings = IngredientList(["$$"])

        assert ings.bad == ["$$"]

    def test_if_ingredient_list_behaves_like_list(self):
        """Ensure that IngredientList behaves like a list."""
        ings = IngredientList([])
        test_ings = ["abc", "def"]
        ings.all = test_ings

        assert len(ings) == 2
        assert list(ings) == test_ings
        for i, _ in enumerate(ings):
            assert ings[i] == test_ings[i]
