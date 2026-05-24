from database import get_connection

conn = get_connection()
cursor = conn.cursor()

# Electronics category = 2

products = [

("Mobile Phone",2,0.25,0.01,"MOB001"),
("Water Bottle",1,1.00,0.05,"BOT001"),
("Book",9,0.80,0.03,"BK001"),
("Keyboard",2,0.70,0.04,"KEY001"),
("Laptop",2,2.00,0.10,"LAP001"),
("Mouse",2,0.20,0.01,"MOU001")

]

for p in products:

    cursor.execute("""
    INSERT INTO products
    (
        product_name,
        category_id,
        weight,
        volume,
        barcode
    )
    VALUES
    (%s,%s,%s,%s,%s)
    """, p)

conn.commit()

print("Products Added")

cursor.close()
conn.close()