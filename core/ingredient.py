from typing import Callable

from core.models import FoodNutrition
from core.search import (
    ParseIngredientError,
    match_one_food,
    match_one_weight,
    parse_ingredient,
)
from core.utils import (
    nutrient_to_tagname,
    nutrient_units,
    split_and_ingredients,
    unit_to_grams,
)


class IngredientError(Exception):
    """Exception raised when creating Ingredient object fails."""

    def __init__(self, to_parse, message):
        super().__init__(message)
        self.to_parse = to_parse


class IngredientList:
    """Parses and stores data about ingredients.

    Class which does everything needed for getting nutrition data.
    Use this class to generate data for your recipe.

    Attributes:
        :raw - list of ingredients provided to be parsed and matched
        :all - all ingredients which were parsed and matched
        :bad - all ingredients which couldnt be parsed or matched
    """

    def __init__(
        self, ingredient_list: list, parser: Callable[[str], dict] = parse_ingredient
    ):
        """
        :ingredient_list - list of ingredients
        :parser - parser which handles user input (ingredient name)
        """
        self.raw = ingredient_list
        self.all = []
        self.bad = []

        ingredient_list = split_and_ingredients(ingredient_list)
        for ing in ingredient_list:
            try:
                self.all.append(Ingredient(ing, parser=parser))
            except IngredientError:
                self.bad.append(ing)
            except ParseIngredientError:
                self.bad.append(ing)

    def __iter__(self):
        return iter(self.all)

    def __getitem__(self, index):
        return self.all[index]

    def __len__(self):
        return len(self.all)

    def total_nutrition(self, servings: int = 1) -> dict:
        """Returns total nutrition.

        Values are rounded with 2 digit precision.

        Args:
            servings: count of servings
        Returns:
            Dictionary with nutrient name as a key and tuple of value, value (per serving) and unit, e.g.
            {
                'PROTEIN': (127.21, 31.80, 'g'),
                'FAT': (124.13, 31.03, 'g'),
                ...
            }
        """
        total_nutrition = {
            "ENERGY": 0,
            "FAT": 0,
            "PROTEIN": 0,
            "CARB": 0,
            "FAT_SAT": 0,
            "FAT_POLY": 0,
            "FAT_MONO": 0,
            "SUGAR": 0,
            "CHOLE": 0,
            "SODIUM": 0,
            "POTAS": 0,
            "FIBER": 0,
        }
        for ing in self.all:
            for nutrient in total_nutrition:
                value = ing.calc_nutrient(nutrient_to_tagname[nutrient])
                if value:
                    total_nutrition[nutrient] += value
        # Round results and create a tuple with value and unit
        for k, v in total_nutrition.items():
            total_nutrition[k] = (
                round(v, 2),
                round(v / servings, 2),
                nutrient_units[k],
            )

        return total_nutrition


class Ingredient:
    """Parses and stores data about an ingredient.

    Class which parses ingredient and stores data about it's weight, amount, nutrition, etc..
    Raises IngredientError if parser couldn't match a Food in database or Food doesn't have any
    FoodWeight to be selected.

    Example usage:
    >>> ing = Ingredient("100 g of chicken breast")
    >>> ing.amount, ing.unit, ing.measurement, ing.name
    (100.0, 'g', '', 'chicken breast')
    >>> ing.weight, ing.matched_food
    (100.0, <Food: #5057 Chicken, broilers or fryers, breast, meat and skin, raw>)
    >>> ing.energy, ing.protein, ing.fat
    (172.0, 20.85, 9.25)

    Attributes:
    :name   - name of ingredient
    :weight - weight in grams
    :matched_food - Food object from database
    :amount - amount of weight
    :unit   - unit (if parsed)
    :raw_input - original string which was used to find matched_food (user input)
    :measurement - measurement (if parsed or no unit) e.g. slice, stick, batch, etc..
    """

    def __init__(self, to_parse: str, parser: Callable[[str], dict] = parse_ingredient):
        """
        :to_parse - ingredient name
        :parser - parser which handles user input (ingredient name)
        """
        self.amount, self.unit, self.measurement, self.name, self.raw_input = parser(
            to_parse
        ).values()
        self.matched_food = match_one_food(self.name)
        if not self.matched_food:
            raise IngredientError(to_parse, f"Couldn't match a food object.")
        if self.unit:
            self.weight = self.amount * unit_to_grams[self.unit]
        else:
            self.weight = self.get_weight()

    def get_weight(self) -> float:
        """
        Returns weight (in grams).
        """
        if not self.matched_food.weight.exists():
            raise IngredientError(
                self.matched_food, f"This food doesn't have any FoodWeight objects."
            )
        matched_weight = match_one_weight(self.matched_food, self.measurement)
        return float(matched_weight.value) * (
            self.amount / float(matched_weight.amount)
        )

    def __repr__(self):  # pragma: no cover
        return f"{self.weight:.2f} g of {self.matched_food}"

    def calc_nutrient(self, tagname: str) -> float:
        """
        Calculates nutrient amount for ingredient's weight

        Args:
            tagname: International Network of Food Data Systems tagname
        Returns:
            Amount of nutrient (in it's corresponding unit) for self.weight
        """
        nutrient = self.get_nutrient_by_tagname(tagname)
        if not nutrient:
            return None
        return float(nutrient.value) / 100 * self.weight

    def get_nutrient_by_tagname(self, tagname: str) -> FoodNutrition:
        """
        Returns nutrient by tagname (if exists in database)
        """
        try:
            return self.matched_food.nutrition.get(tagname=tagname)
        except FoodNutrition.DoesNotExist:
            return None

    @property
    def energy(self) -> float:
        return self.calc_nutrient("ENERC_KCAL")

    @property
    def protein(self) -> float:
        return self.calc_nutrient("PROCNT")

    @property
    def fat(self) -> float:
        return self.calc_nutrient("FAT")

    @property
    def fat_sat(self) -> float:
        return self.calc_nutrient("FASAT")

    @property
    def fat_poly(self) -> float:
        return self.calc_nutrient("FAPU")

    @property
    def fat_mono(self) -> float:
        return self.calc_nutrient("FAMS")

    @property
    def carb(self) -> float:
        return self.calc_nutrient("CHOCDF")

    @property
    def sugar(self) -> float:
        return self.calc_nutrient("SUGAR")

    @property
    def chol(self) -> float:
        return self.calc_nutrient("CHOLE")

    @property
    def sodium(self) -> float:
        return self.calc_nutrient("NA")

    @property
    def potas(self) -> float:
        return self.calc_nutrient("K")

    @property
    def fiber(self) -> float:
        return self.calc_nutrient("FIBTG")
