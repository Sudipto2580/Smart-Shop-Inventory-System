from database import get_connection

conn = get_connection()
cursor = conn.cursor()

# ==================================
# DROP TABLES
# ==================================

cursor.execute("DROP TABLE IF EXISTS stock_alerts CASCADE")
cursor.execute("DROP TABLE IF EXISTS product_location_history CASCADE")
cursor.execute("DROP TABLE IF EXISTS yolo_product_mapping CASCADE")
cursor.execute("DROP TABLE IF EXISTS shelf_allocation_log CASCADE")
cursor.execute("DROP TABLE IF EXISTS transactions CASCADE")
cursor.execute("DROP TABLE IF EXISTS inventory CASCADE")
cursor.execute("DROP TABLE IF EXISTS products CASCADE")
cursor.execute("DROP TABLE IF EXISTS categories CASCADE")
cursor.execute("DROP TABLE IF EXISTS shelves CASCADE")

# ==================================
# CATEGORIES
# ==================================

cursor.execute("""
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE
)
""")

# ==================================
# PRODUCTS
# ==================================

cursor.execute("""
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) UNIQUE,
    category_id INTEGER,
    weight REAL,
    volume REAL,
    barcode VARCHAR(100) UNIQUE,
    image_path TEXT,

    FOREIGN KEY(category_id)
    REFERENCES categories(category_id)
)
""")

# ==================================
# SHELVES
# ==================================

cursor.execute("""
CREATE TABLE shelves (
    shelf_id SERIAL PRIMARY KEY,
    shelf_name VARCHAR(20) UNIQUE,
    max_capacity REAL,
    used_capacity REAL,
    location_row VARCHAR(10),
    location_column INTEGER
)
""")

# ==================================
# INVENTORY
# ==================================

cursor.execute("""
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INTEGER,
    shelf_id INTEGER,
    quantity INTEGER,
    total_weight REAL,

    FOREIGN KEY(product_id)
    REFERENCES products(product_id),

    FOREIGN KEY(shelf_id)
    REFERENCES shelves(shelf_id)
)
""")

# ==================================
# TRANSACTIONS
# ==================================

cursor.execute("""
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    product_id INTEGER,
    action VARCHAR(100),
    quantity INTEGER,
    shelf_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ==================================
# SHELF ALLOCATION LOG
# ==================================

cursor.execute("""
CREATE TABLE shelf_allocation_log (
    allocation_id SERIAL PRIMARY KEY,
    product_id INTEGER,
    shelf_id INTEGER,
    assigned_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ==================================
# PRODUCT HISTORY
# ==================================

cursor.execute("""
CREATE TABLE product_location_history (
    history_id SERIAL PRIMARY KEY,
    product_id INTEGER,
    shelf_id INTEGER,
    quantity INTEGER,
    moved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ==================================
# STOCK ALERTS
# ==================================

cursor.execute("""
CREATE TABLE stock_alerts (
    alert_id SERIAL PRIMARY KEY,
    product_id INTEGER,
    minimum_stock INTEGER
)
""")

# ==================================
# YOLO PRODUCT MAPPING
# ==================================

cursor.execute("""
CREATE TABLE yolo_product_mapping (
    yolo_name VARCHAR(100) PRIMARY KEY,
    product_id INTEGER
)
""")

# ==================================
# INSERT CATEGORIES
# ==================================

categories = [
("Grocery",),
("Electronics",),
("Cosmetics",),
("Beverages",),
("Stationery",),
("Clothing",),
("Toys",),
("Automotive",),
("Books",),
("Sports",),
("Healthcare",),
("Home Decor",),
("Garden",),
("Pet Supplies",),
("Office Supplies",),
("Tools",)
]

cursor.executemany(
"""
INSERT INTO categories(category_name)
VALUES (%s)
""",
categories
)

# ==================================
# INSERT 16 SHELVES
# ==================================

shelves = [

("A1",100,0,"A",1),
("A2",100,0,"A",2),
("A3",150,0,"A",3),
("A4",200,0,"A",4),

("B1",100,0,"B",1),
("B2",100,0,"B",2),
("B3",150,0,"B",3),
("B4",200,0,"B",4),

("C1",100,0,"C",1),
("C2",100,0,"C",2),
("C3",150,0,"C",3),
("C4",200,0,"C",4),

("D1",100,0,"D",1),
("D2",100,0,"D",2),
("D3",150,0,"D",3),
("D4",200,0,"D",4)

]

cursor.executemany("""
INSERT INTO shelves
(
shelf_name,
max_capacity,
used_capacity,
location_row,
location_column
)
VALUES (%s,%s,%s,%s,%s)
""", shelves)

conn.commit()

print("SUPABASE DATABASE CREATED SUCCESSFULLY")

cursor.close()
conn.close()