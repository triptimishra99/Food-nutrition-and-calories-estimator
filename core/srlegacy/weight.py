import json

from core.models import Food, FoodNutrition, FoodWeight

COLUMN_NAMES = (  # Corresponding origin column names to model fields
    "NDB_No",  # food
    "Seq",  # -
    "Amount",  # amount
    "Msre_desc",  # desc
    "Gm_Wgt",  # value
    "Num_Data_Pts",  # -
    "Deviation",  # -
)

CONVERT_TYPES = {
    "NDB_No": int,
    "Seq": int,
    "Amount": float,
    "Msre_desc": str,
    "Gm_Wgt": float,
    "Num_Data_Pts": int,
    "Deviation": float,
}

COLUMN_TO_FIELD = {
    "NDB_No": "food",
    "Amount": "amount",
    "Msre_desc": "desc",
    "Gm_Wgt": "value",
}


def parse_row(row):
    row = row.strip().split("^")
    row = [r.strip("~") for r in row]
    row = [r if r else None for r in row]
    row[0] = row[0].lstrip("0")
    row = dict(zip(COLUMN_NAMES, row))
    row = {k: CONVERT_TYPES[k](v) if v else v for k, v in row.items()}
    row = {COLUMN_TO_FIELD[k]: v for k, v in row.items() if k in COLUMN_TO_FIELD.keys()}
    row["food"] = Food.objects.get(pk=row["food"])
    return row


def main(filename):
    to_add = []
    with open(filename, encoding="cp1250") as f:
        for i, row in enumerate(f):
            parsed = parse_row(row)
            to_add.append(FoodWeight(**parsed))
            # Bulk create every 5000 entries to save RAM
            if i % 5000 == 0:
                FoodWeight.objects.bulk_create(to_add)
                to_add.clear()
    FoodWeight.objects.bulk_create(to_add)
