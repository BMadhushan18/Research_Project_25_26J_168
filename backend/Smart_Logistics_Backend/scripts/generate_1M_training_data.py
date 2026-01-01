"""Generate 1,000,000 synthetic BOQ-like rows in a memory-efficient (chunked) way.
Usage:
    python scripts/generate_1M_training_data.py --out data/training_data_1M_rows.csv --chunk-size 10000 --seed 42

Note: This will write the CSV in chunks to avoid allocating the full dataset in memory.
"""
import argparse
import csv
import random
import math
from pathlib import Path

VEHICLE_COLS = ['Excavators', 'Bulldozers', 'Cranes', 'Dump Trucks', 'Loaders', 'Graders', 'Compactors', 'Pavers', 'Rollers', 'Trenchers', 'Skid Steers', 'Backhoe Loaders', 'Telehandlers', 'Forklifts', 'Scrapers', 'Concrete Mixers', 'Pile Drivers', 'Asphalt Mills', 'Manlifts', 'Drilling Rigs']

HEADERS = [
    'sheet', 'item', 'description', 'quantity', 'unit', 'rate', 'amount', 'labor_types', 'vehicles', 'nlp_entities',
    'total_fuel_liters', 'estimated_hours', 'estimated_cost_lkr', 'labor_hours', 'employee_count',
    'excavation_volume', 'site_area', 'wall_area', 'floor_area', 'concrete_volume', 'steel_quantity', 'brick_quantity',
    'total_cement', 'total_sand', 'building_complexity'
] + VEHICLE_COLS + ['vehicles_needed', 'masons', 'welders', 'laborers', 'fuel_liters', 'estimated_hours2', 'estimated_cost']

UNIT_OPTIONS = ['m3', 'kg', 'units', 'Item', 'Cube', 'm2', 'm', 'No', 'Lump Sum', 'bag']
LABOR_OPTIONS = ['Skilled', 'Unskilled', 'Semi-skilled', 'Professional', 'Skilled,Unskilled', 'Unskilled,Semi-skilled', 'Skilled,Semi-skilled']
VEHICLE_OPTIONS = ['Excavator', 'Dump Truck', 'Concrete Mixer Truck', 'Crane', 'Loader', 'Tipper Truck', 'Flatbed Truck', 'None', 'Loader,Mixer', 'Crane,Trailer']


def gen_row(i):
    quantity = random.uniform(1, 500)
    rate = random.uniform(1000, 200000)
    amount = quantity * rate
    unit = random.choice(UNIT_OPTIONS)
    row = {
        'sheet': random.choice(['SYN', 'BOQ', 'SUMMARY', 'prelims', 'Concrete', 'Masonry']),
        'item': f'Item_{i % 200}',
        'description': 'Synthetic entry from BOQ patterns',
        'quantity': round(quantity, 6),
        'unit': unit,
        'rate': round(rate, 6),
        'amount': round(amount, 6),
        'labor_types': random.choice(LABOR_OPTIONS),
        'vehicles': random.choice(VEHICLE_OPTIONS),
        'nlp_entities': random.choice(['', 'QUANTITY', 'MONEY', 'CARDINAL']),
        'total_fuel_liters': round(random.uniform(10, 1000), 3),
        'estimated_hours': round(random.uniform(1, 500), 3),
        'estimated_cost_lkr': round(random.uniform(100000, 50000000), 3),
        'labor_hours': round(random.uniform(1, 500), 3),
        'employee_count': random.randint(1, 100),
        'excavation_volume': round(quantity if unit in ['m3', 'Cube'] else random.uniform(50, 500), 3),
        'site_area': round(random.uniform(200, 2000), 3),
        'wall_area': round(random.uniform(100, 1000), 3),
        'floor_area': round(random.uniform(150, 1500), 3),
        'concrete_volume': round(random.uniform(20, 200), 3),
        'steel_quantity': round(random.uniform(200, 2000), 3),
        'brick_quantity': random.randint(500, 5000),
        'total_cement': round(random.uniform(1000, 10000), 3),
        'total_sand': round(random.uniform(500, 5000), 3),
        'building_complexity': random.randint(1, 5),
    }
    # vehicle presence
    vehicles_sum = 0
    for col in VEHICLE_COLS:
        val = random.randint(0, 5)
        row[col] = val
        vehicles_sum += val
    row['vehicles_needed'] = round(vehicles_sum * random.uniform(0.8, 1.2), 3)
    row['masons'] = random.randint(2, 20)
    row['welders'] = random.randint(1, 10)
    row['laborers'] = random.randint(5, 50)
    row['fuel_liters'] = row['total_fuel_liters']
    row['estimated_hours2'] = row['estimated_hours']
    row['estimated_cost'] = row['estimated_cost_lkr']
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='data/training_data_1M_rows.csv')
    parser.add_argument('--n', type=int, default=1000000)
    parser.add_argument('--chunk-size', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
        writer.writeheader()
        chunk = []
        for i in range(args.n):
            row = gen_row(i)
            chunk.append(row)
            if len(chunk) >= args.chunk_size:
                writer.writerows(chunk)
                chunk = []
        if chunk:
            writer.writerows(chunk)
    print('Wrote', args.n, 'rows to', out_path)

if __name__ == '__main__':
    main()
