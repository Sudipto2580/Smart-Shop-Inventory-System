from database import get_connection

conn = get_connection()
cursor = conn.cursor()

# ==========================
# DROP OLD TABLES
# ==========================

cursor.execute("DROP TABLE IF EXISTS yolo_product_mapping")
cursor.execute("DROP TABLE IF EXISTS shelf_allocation_log")
cursor.execute("DROP TABLE IF EXISTS transactions")
cursor.execute("DROP TABLE IF EXISTS inventory")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS categories")
cursor.execute("DROP TABLE IF EXISTS shelves")

# ==========================
# CATEGORIES
# ==========================

cursor.execute("""
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE
)
""")

# ==========================
# PRODUCTS
# ==========================

cursor.execute("""
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT UNIQUE,
    category_id INTEGER,
    weight REAL,
    volume REAL,
    barcode TEXT UNIQUE,
    FOREIGN KEY(category_id)
    REFERENCES categories(category_id)
)
""")

# ==========================
# SHELVES
# ==========================

cursor.execute("""
CREATE TABLE shelves (
    shelf_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shelf_name TEXT UNIQUE,
    max_capacity REAL,
    used_capacity REAL,
    location_row TEXT,
    location_column INTEGER
)
""")

# ==========================
# INVENTORY
# ==========================

cursor.execute("""
CREATE TABLE inventory (
    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
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

# ==========================
# TRANSACTIONS
# ==========================

cursor.execute("""
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    action TEXT,
    quantity INTEGER,
    shelf_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# ==========================
# SHELF ALLOCATION LOG
# ==========================

cursor.execute("""
CREATE TABLE shelf_allocation_log (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    shelf_id INTEGER,
    assigned_time DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
# ==========================
# YOLO PRODUCT MAPPING
# ==========================

cursor.execute("""
CREATE TABLE yolo_product_mapping (
    yolo_name TEXT PRIMARY KEY,
    product_id INTEGER,
    FOREIGN KEY(product_id)
    REFERENCES products(product_id)
)
""")
# ==========================
# INSERT CATEGORIES
# ==========================

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
    "INSERT INTO categories(category_name) VALUES(?)",
    categories
)
#=========================================================
#PRODUCT MAPPING
#=========================================================

# ==========================
# INSERT 16 SHELVES
# ==========================

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
VALUES(?,?,?,?,?)
""", shelves)

conn.commit()
conn.close()

print("Professional Warehouse Database Created Successfully")