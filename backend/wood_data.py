import pandas as pd
import random

# =====================================================
# Grade A base prices (LKR per cubic foot)
# =====================================================
GRADE_A_PRICES = {
    "Structural Framing": {
        "jak": 1000,
        "burutha": 600,
        "kubuk": 2000,
        "teak": 1200,
        "kempas": 2800,
        "thulan": 3000,
        "microo": 2000,
        "mahoganii": 1050,
        "mango": 400
    },
    "Door/window": {
        "jak": 850,
        "burutha": 500,
        "teak": 1200,
        "kempas": 1500,
        "thulan": 1500,
        "microo": 1000,
        "mahoganii": 750,
        "ginisapu": 250,
        "mango": 200
    },
    "Roofing Components": {
        "lunumidella": 500,
        "ginisapu": 450,
        "pinewood": 600,
        "kempas": 1200
    }
}

# =====================================================
# Wood location categories
# =====================================================
INDOOR_WOODS = [
    "jak", "mahoganii", "ginisapu", "pinewood",
    "mango", "kempas", "thulan", "microo", "rubber"
]

OUTDOOR_WOODS = [
    "kubuk", "burutha", "teak", "kaluwara"
]

SEMI_WOODS = [
    "jak", "teak", "kempas", "burutha", "mahoganii"
]

# =====================================================
# Helper: Determine Location
# =====================================================
def determine_location(wood):
    if wood in SEMI_WOODS:
        return "Semi"
    elif wood in INDOOR_WOODS:
        return "Indoor"
    elif wood in OUTDOOR_WOODS:
        return "Outdoor"
    else:
        return random.choice(["Indoor", "Outdoor", "Semi"])

# =====================================================
# Generate Dataset
# =====================================================
rows = []
TOTAL_ROWS = 5000

for _ in range(TOTAL_ROWS):
    building_type = random.choice(list(GRADE_A_PRICES.keys()))
    wood = random.choice(list(GRADE_A_PRICES[building_type].keys()))
    grade = random.choice(["A", "B", "C"])

    base_price = GRADE_A_PRICES[building_type][wood]

    # Grade-based pricing rules
    if grade == "A":
        price = base_price
    elif grade == "B":
        price = int(base_price * random.uniform(0.75, 0.9))
    else:  # Grade C
        price = int(base_price * random.uniform(0.55, 0.7))

    rows.append({
        "Price per cubic foot (LKR)": price,
        "Size (cu.ft)": round(random.uniform(1.0, 30.0), 2),
        "Wood Species": wood,
        "Wood Grade": grade,
        "Location": determine_location(wood),
        "Building Type": building_type
    })

# =====================================================
# Save to CSV
# =====================================================
df = pd.DataFrame(rows)
df.to_csv("wood_price_dataset_3000.csv", index=False)

print("Dataset generated successfully!")
print(df.head())
