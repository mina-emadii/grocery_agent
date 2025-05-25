import csv
from database_setup import add_product, session, Product
from sqlalchemy import create_engine
from tqdm import tqdm
import time

def load_fdc(path, batch_size=1000):
    print(f"Loading data from {path}...")
    start_time = time.time()
    
    # Get total number of rows for progress bar
    with open(path, newline='', encoding='utf8') as csvfile:
        total_rows = sum(1 for _ in csvfile) - 1  # Subtract header row
    
    products_to_add = []
    products_to_update = []
    
    with open(path, newline='', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Create progress bar
        pbar = tqdm(total=total_rows, desc="Processing products")
        
        for row in reader:
            # Use gtin_upc or fdc_id as the identifier
            upc = row['gtin_upc'] or row['fdc_id']
            name = row['short_description']
            ingredients = row.get('ingredients') or ''
            
            # Build nutrient map from columns like 'protein_g', 'fat_g', etc.
            nutrients = {}
            for col in ['protein_g','fat_g','carbohydrate_g']:
                if row.get(col):
                    nutrients[col.replace('_g','').capitalize()] = row[col] + ' g'
            
            # Use branded_food_category for categories
            categories = [row['branded_food_category']] if row.get('branded_food_category') else []
            dietary = []
            
            # Naively tag organic / halal / gluten_free based on description and ingredients
            if 'organic' in name.lower(): 
                dietary.append('organic')
            if 'wheat' not in ingredients.lower(): 
                dietary.append('gluten_free')
            if 'pork' not in ingredients.lower(): 
                dietary.append('halal')
            
            product_data = {
                'upc': upc,
                'name': name,
                'ingredients': ingredients,
                'nutrients': nutrients,
                'categories': categories,
                'dietary': dietary,
                'price': None,
                'store': None,
                'last_updated': None
            }
            
            # Check if product exists
            existing_product = session.query(Product).filter_by(upc=upc).first()
            if existing_product:
                products_to_update.append(product_data)
            else:
                products_to_add.append(product_data)
            
            # Process in batches
            if len(products_to_add) + len(products_to_update) >= batch_size:
                _process_batch(products_to_add, products_to_update)
                products_to_add = []
                products_to_update = []
            
            pbar.update(1)
        
        # Process remaining items
        if products_to_add or products_to_update:
            _process_batch(products_to_add, products_to_update)
        
        pbar.close()
    
    end_time = time.time()
    print(f"\nCompleted in {end_time - start_time:.2f} seconds")

def _process_batch(products_to_add, products_to_update):
    """Process a batch of products to add or update."""
    try:
        # Bulk insert new products
        if products_to_add:
            session.bulk_insert_mappings(Product, products_to_add)
        
        # Bulk update existing products
        if products_to_update:
            session.bulk_update_mappings(Product, products_to_update)
        
        session.commit()
    except Exception as e:
        print(f"Error processing batch: {e}")
        session.rollback()

if __name__ == '__main__':
    load_fdc('data/branded_food.csv') 