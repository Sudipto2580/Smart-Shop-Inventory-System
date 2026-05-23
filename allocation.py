from database import get_connection


def assign_shelf(total_weight):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT shelf_id,
           shelf_name,
           max_capacity,
           used_capacity
    FROM shelves
    ORDER BY shelf_id
    """)

    shelves = cursor.fetchall()

    for shelf in shelves:

        shelf_id = shelf[0]
        shelf_name = shelf[1]
        max_capacity = shelf[2]
        used_capacity = shelf[3]

        remaining = max_capacity - used_capacity

        if remaining >= total_weight:

            new_used = used_capacity + total_weight

            cursor.execute("""
            UPDATE shelves
            SET used_capacity=?
            WHERE shelf_id=?
            """,
            (
                new_used,
                shelf_id
            ))

            conn.commit()

            conn.close()

            return shelf_id, shelf_name

    conn.close()

    return None, None