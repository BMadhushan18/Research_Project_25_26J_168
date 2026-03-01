import random
import pandas as pd

# Number of records
NUM_RECORDS = 4000

# Brand lists (from your specification)
INTERIOR_BRANDS = [
    "Nippon", "Multilac", "Dulux", "Robbialac", "JAT", "Asian Paints Causeway"
]

FLOOR_BRANDS = [
    "Causeway", "Lankem Robbialac", "Robbialac",
    "Nippon Epoxy", "Nippon Water Based",
    "Nippon Floor Wax Polish", "Nippon Floor Paint",
    "Dulux QD Floor Paints"
]

OUTDOOR_BRANDS = [
    "MULTILAC 3IN1", "Multilac Ultra Flex 1000", "Multilac Nano Shield 900",
    "Multilac Nano Sealer 700", "MULTILAC MULTI PROTECTO",
    "Dulux Aquatech", "Causeway SmartCare Aqua Safe",
    "WAPP Waterproofing Paint", "Nippon Flex 100",
    "Nippon Flex 400 H/D Elastomeric", "JAT Exterior",
    "Dulux Superkote", "Dulux Weathershield",
    "Nippon Durafresh", "Multilac Weather Guard",
    "Nippolac Weatherproof", "Causeway Weatherproof",
    "Nippon Atom 2 in 1"
]

WOOD_BRANDS = [
    "Nippolac Water Based", "JAT Water Base",
    "Nippon Water Base", "Dulux Water Base",
    "Robbialac Water Base"
]

GRADES = ["Economy", "Standard", "Premium"]

LOCATIONS = ["indoor", "floor", "outdoor", "wood"]

# Price logic by location and grade
PRICE_RANGES = {
    "indoor": {"Economy": (40, 50), "Standard": (51, 60), "Premium": (61, 70)},
    "wood": {"Economy": (50, 60), "Standard": (61, 70), "Premium": (71, 80)},
    "floor": {"Economy": (70, 85), "Standard": (86, 100), "Premium": (101, 120)},
    "outdoor": {"Economy": (65, 75), "Standard": (76, 85), "Premium": (86, 100)}
}

data = []

for _ in range(NUM_RECORDS):
    location = random.choice(LOCATIONS)
    grade = random.choice(GRADES)
    wall_size = random.randint(80, 600)

    if location == "indoor":
        brand = random.choice(INTERIOR_BRANDS)
    elif location == "floor":
        brand = random.choice(FLOOR_BRANDS)
    elif location == "outdoor":
        brand = random.choice(OUTDOOR_BRANDS)
    else:
        brand = random.choice(WOOD_BRANDS)

    price_min, price_max = PRICE_RANGES[location][grade]
    price = random.randint(price_min, price_max)

    data.append([
        wall_size,
        price,
        location,
        brand,
        grade
    ])

# Create DataFrame
df = pd.DataFrame(data, columns=[
    "WallSize_sqft",
    "PricePerSqft_LKR",
    "Location",
    "PaintBrand",
    "PaintGrade"
])

# Save to CSV
df.to_csv("sri_lanka_paint_dataset_1000.csv", index=False)

print("Dataset generated: sri_lanka_paint_dataset_1000.csv")
