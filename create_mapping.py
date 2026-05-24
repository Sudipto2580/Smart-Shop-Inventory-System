from database import get_connection

conn = get_connection()
cursor = conn.cursor()

mappings = [

("cell phone",1),
("bottle",2),
("book",3),
("keyboard",4),
("laptop",5),
("mouse",6)

]

for m in mappings:

    cursor.execute("""
    INSERT INTO yolo_product_mapping
    (
        yolo_name,
        product_id
    )
    VALUES
    (%s,%s)
    ON CONFLICT (yolo_name)
    DO NOTHING
    """, m)

conn.commit()

print("Mappings Added")

cursor.close()
conn.close()