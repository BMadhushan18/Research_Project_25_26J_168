import os
import json
import random
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ML_DIR = DATA_DIR / "ml"
NLP_DIR = DATA_DIR / "nlp"

os.makedirs(ML_DIR, exist_ok=True)
os.makedirs(NLP_DIR, exist_ok=True)

# Generate ML synthetic CSV
ml_file = ML_DIR / "synthetic_ml.csv"
with open(ml_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Features: terrain (0 urban,1 rural), distance_km, material_tons, wall_length_m, wall_height_m
    # Targets: fuel_liters, labor_hours, total_cost, vehicle_count
    header = ["terrain","distance_km","material_tons","wall_length_m","wall_height_m",
              "fuel_liters","labor_hours","total_cost","vehicle_count"]
    writer.writerow(header)
    random.seed(0)
    for i in range(1000):
        terrain = random.choice([0,1])
        distance = round(random.uniform(1,50),2)
        material = round(random.uniform(0.1,50),2)
        wall_len = round(random.uniform(0,50),2)
        wall_h = round(random.uniform(0,6),2)
        # simple generative formulas
        fuel = round(2.0 * material + 0.5 * distance + 5*terrain + random.gauss(0,2),2)
        hours = round(10 * material + 2 * wall_len * wall_h + random.gauss(0,5),2)
        cost = int(5000 * material + 200 * hours + 100 * terrain + random.randint(0,1000))
        vehicles = max(1, int(fuel // 40))
        writer.writerow([terrain,distance,material,wall_len,wall_h,fuel,hours,cost,vehicles])

print(f"Wrote ML synthetic data to {ml_file}")

# Generate NLP synthetic documents and annotations
# Create simple BOQ-like lines and corresponding annotations (item, qty, unit)
items = ["cement","steel","sand","bricks","gravel","paint","tiles"]
annotations = []
for i in range(200):
    num_lines = random.randint(3,15)
    lines = []
    ann = {"doc_id": f"doc_{i}", "text":"", "entities": []}
    text_parts = []
    cursor = 0
    for j in range(num_lines):
        item = random.choice(items)
        qty = random.randint(1,500)
        unit = random.choice(["kg","ton","m3","pcs","bag"])
        line = f"{item} - {qty} {unit}\\n"
        text_parts.append(line)
        # entity span start/end
        start = cursor
        end = cursor + len(item)
        ann["entities"].append([start,end,"MATERIAL_NAME"])
        cursor += len(line)
    ann["text"] = "".join(text_parts)
    annotations.append(ann)
    with open(NLP_DIR / f"doc_{i}.txt","w",encoding="utf-8") as df:
        df.write(ann["text"])

with open(NLP_DIR / "annotations.json","w",encoding="utf-8") as af:
    json.dump(annotations, af, indent=2)

print(f"Wrote NLP synthetic docs to {NLP_DIR}")