import random
import pandas as pd

# =====================================
# Configuration
# =====================================
NUM_RECORDS = 1000   # change to 3000 if required

PREMIUM_BRANDS = [
    "INSEE Skim Coat",
    "SF Skim Coat",
    "Swisstek Skim Coat",
    "INSEE Skim cement Coat",
    "Tokyo plaster master"
]

INDOOR_BRANDS = [
    "NIPPOFLEX skim coat",
    "NIPPON skim coat",
    "Multilac Skim Coat",
    "ASIANPAINT Skim Coat",
    "INSEE Skim Coat",
    "SF Skim Coat",
    "Swisstek Skim Coat"
]

OUTDOOR_BRANDS = [
    "INSEE Skim cement Coat",
    "Tokyo plaster master"
]

PRICE_RANGES = {
    "Indoor": (650, 850),
    "Outdoor": (800, 1000)
}

# =====================================
# Dataset generation
# =====================================
data = []

for _ in range(NUM_RECORDS):

    location = random.choice(["Indoor", "Outdoor"])
    wall_size = random.randint(80, 800)

    # Brand selection
    if location == "Indoor":
        brand = random.choice(INDOOR_BRANDS)
        base_price = random.randint(*PRICE_RANGES["Indoor"])
    else:
        brand = random.choice(OUTDOOR_BRANDS)
        base_price = random.randint(*PRICE_RANGES["Outdoor"])

    # Wall size price adjustment
    if wall_size > 500:
        price = int(base_price * random.uniform(0.90, 0.95))
    elif wall_size < 150:
        price = int(base_price * random.uniform(1.05, 1.10))
    else:
        price = base_price

    # =====================================
    # Enforce premium brand pricing (>800)
    # =====================================
    if brand in PREMIUM_BRANDS:
        price = max(price, random.randint(820, 1000))

    data.append([
        wall_size,
        price,
        location,
        brand
    ])

# =====================================
# Create DataFrame
# =====================================
df = pd.DataFrame(data, columns=[
    "WallSize_sqft",
    "PricePerSqft_LKR",
    "Location",
    "Brand"
])

# =====================================
# Save CSV
# =====================================
df.to_csv("sri_lanka_skim_coat_dataset_5000.csv", index=False)

print("Dataset generated successfully!")
print(df.head())
