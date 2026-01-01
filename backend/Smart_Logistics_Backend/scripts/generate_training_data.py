"""Generate synthetic 10,000-row BOQ-derived dataset and a derived CSV compatible with scripts/train.py
Usage: run from project root or from this folder using the configured Python.
Produces:
 - data/training_data_10000_rows.csv  (full wide schema)
 - data/training_for_model.csv       (columns: boq_text,machinery,vehicles,skilled,unskilled)
"""
import pandas as pd
import numpy as np
import random
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(OUT_DIR, exist_ok=True)

# Full schema headers
headers = [
    'sheet', 'item', 'description', 'quantity', 'unit', 'rate', 'amount', 'labor_types', 'vehicles', 'nlp_entities',
    'total_fuel_liters', 'estimated_hours', 'estimated_cost_lkr', 'labor_hours', 'employee_count',
    'excavation_volume', 'site_area', 'wall_area', 'floor_area', 'concrete_volume', 'steel_quantity', 'brick_quantity',
    'total_cement', 'total_sand', 'building_complexity',
    'Excavators', 'Bulldozers', 'Cranes', 'Dump Trucks', 'Loaders', 'Graders', 'Compactors', 'Pavers', 'Rollers',
    'Trenchers', 'Skid Steers', 'Backhoe Loaders', 'Telehandlers', 'Forklifts', 'Scrapers', 'Concrete Mixers',
    'Pile Drivers', 'Asphalt Mills', 'Manlifts', 'Drilling Rigs',
    'vehicles_needed', 'masons', 'welders', 'laborers', 'fuel_liters', 'estimated_hours2', 'estimated_cost'
]

labor_options = ['Skilled', 'Unskilled', 'Semi-skilled', 'Professional', 'Skilled,Semi-skilled', 'Skilled,Unskilled', 'Unskilled,Semi-skilled', 'Skilled,Professional']
vehicle_options = ['Large Truck', 'Trailer', 'None', 'Excavator', 'Crane', 'Loader,Mixer', 'Crane,Trailer']
unit_options = ['units', 'm3', 'kg', 'pieces', 'bag']
vehicle_presence_cols = headers[25:45]

N = 10000
rows = []
for i in range(N):
    quantity = float(np.round(random.uniform(10, 500), 6))
    unit = random.choice(unit_options)
    rate = float(np.round(random.uniform(10000, 200000), 6))
    amount = float(np.round(quantity * rate, 6))
    labor_types = random.choice(labor_options)
    vehicles = random.choice(vehicle_options)

    row = {
        'sheet': 'SYN',
        'item': f'Item_{i % 200}',
        'description': 'Synthetic entry',
        'quantity': quantity,
        'unit': unit,
        'rate': rate,
        'amount': amount,
        'labor_types': labor_types,
        'vehicles': vehicles,
        'nlp_entities': '',
        'total_fuel_liters': float(np.round(random.uniform(10, 1000), 3)),
        'estimated_hours': float(np.round(random.uniform(1, 500), 3)),
        'estimated_cost_lkr': float(np.round(random.uniform(100000, 50000000), 3)),
        'labor_hours': float(np.round(random.uniform(1, 500), 3)),
        'employee_count': int(random.randint(1, 100)),
        'excavation_volume': float(np.round(quantity if unit == 'm3' else random.uniform(50, 500), 3)),
        'site_area': float(np.round(random.uniform(200, 2000), 3)),
        'wall_area': float(np.round(random.uniform(100, 1000), 3)),
        'floor_area': float(np.round(random.uniform(150, 1500), 3)),
        'concrete_volume': float(np.round(random.uniform(20, 200), 3)),
        'steel_quantity': float(np.round(random.uniform(200, 2000), 3)),
        'brick_quantity': int(random.randint(500, 5000)),
        'total_cement': float(np.round(random.uniform(1000, 10000), 3)),
        'total_sand': float(np.round(random.uniform(500, 5000), 3)),
        'building_complexity': int(random.randint(1, 5))
    }
    # Random vehicle presence (0-5)
    for col in vehicle_presence_cols:
        row[col] = int(random.randint(0, 5))

    vehicles_sum = sum(row[col] for col in vehicle_presence_cols)
    row['vehicles_needed'] = float(np.round(vehicles_sum * random.uniform(0.8, 1.2), 3))
    row['masons'] = int(random.randint(2, 20))
    row['welders'] = int(random.randint(1, 10))
    row['laborers'] = int(random.randint(5, 50))
    row['fuel_liters'] = row['total_fuel_liters']
    row['estimated_hours2'] = row['estimated_hours']
    row['estimated_cost'] = row['estimated_cost_lkr']

    rows.append(row)

full_df = pd.DataFrame(rows, columns=headers)
full_csv = os.path.join(OUT_DIR, 'training_data_10000_rows.csv')
full_df.to_csv(full_csv, index=False)
print('Saved full synthetic CSV to:', full_csv)

# Derive a smaller training CSV compatible with scripts/train.py
# Map: boq_text (concatenate item, description, quantity, unit, labor_types),
# machinery <- vehicles, vehicles <- vehicles, skilled <- masons + welders, unskilled <- laborers
train_df = pd.DataFrame()
train_df['boq_text'] = full_df.apply(lambda r: f"{r['item']} {r['description']} qty:{r['quantity']} {r['unit']} vehicles:{r['vehicles']} labor:{r['labor_types']}", axis=1)
train_df['machinery'] = full_df['vehicles'].fillna('').apply(lambda s: ';'.join([x.strip() for x in str(s).split(',') if x and x.lower() != 'none']))
train_df['vehicles'] = train_df['machinery']
# Derive labour_roles based on counts
def make_roles(row):
    roles = []
    if row['masons'] > 0:
        roles.append('mason')
    if row['welders'] > 0:
        roles.append('welder')
    if row['laborers'] > 0:
        roles.append('labourer')
    # add operator if heavy machinery present
    if row['Excavators'] > 0 or row['Cranes'] > 0 or row['Loaders'] > 0:
        roles.append('operator')
    # supervisor sometimes
    if random.random() < 0.2:
        roles.append('supervisor')
    return ';'.join(roles)

train_df['labour_roles'] = full_df.apply(make_roles, axis=1)

train_df['skilled'] = (full_df['masons'] + full_df['welders']).astype(int)
train_df['unskilled'] = full_df['laborers'].astype(int)

small_csv = os.path.join(OUT_DIR, 'training_for_model.csv')
train_df.to_csv(small_csv, index=False)
print('Saved derived training CSV to:', small_csv)
print('Sample:')
print(train_df.head(10).to_csv(index=False))
