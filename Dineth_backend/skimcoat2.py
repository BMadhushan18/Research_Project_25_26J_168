import random
import csv

# Brand lists
INDOOR_BRANDS = [
    "NIPPOFLEX skim coat",
    "NIPPON skim coat",
    "INSEE Skim Coat",
    "SF Skim Coat",
    "Swisstek Skim Coat",
    "Maxbond Skim Coat",
    "Multilac Skim Coat",
    "ASIANPAINT Skim Coat"
]

OUTDOOR_BRANDS = [
    "INSEE Skim cement Coat",
    "Tokyo plaster master"
]

# Other parameters
wall_sizes = range(200, 1000)
prices = [500, 750, 1000]
locations = ["indoor", "outdoor"]
surface_types = ["concrete", "cement plaster", "old wall"]
surface_conditions = ["new", "uneven", "cracked", "repaired"]
finish_levels = ["basic", "smooth", "ultra smooth"]
moisture_levels = ["low", "medium", "high"]
durability_levels = ["low", "medium", "high"]

# Create CSV file
with open("skim_coat_dataset_1000.csv", "w", newline="") as file:
    writer = csv.writer(file)

    # Header
    writer.writerow([
        "WallSize_sqft",
        "PricePerSqft_LKR",
        "Location",
        "Brand",
        "SurfaceType",
        "SurfaceCondition",
        "FinishLevel",
        "MoistureLevel",
        "DurabilityRequirement"
    ])

    # Generate records
    for _ in range(3000):
        location = random.choice(locations)

        if location == "indoor":
            brand = random.choice(INDOOR_BRANDS)
        else:
            brand = random.choice(OUTDOOR_BRANDS)

        writer.writerow([
            random.choice(wall_sizes),
            random.choice(prices),
            location,
            brand,
            random.choice(surface_types),
            random.choice(surface_conditions),
            random.choice(finish_levels),
            random.choice(moisture_levels),
            random.choice(durability_levels)
        ])

print("skim_coat_dataset_1000.csv generated successfully")