from ultralytics import YOLO
import cv2
import time
from database import get_connection
from allocation import assign_shelf

last_saved = None
last_saved_time = 0

# ==========================
# LOAD YOLO MODEL
# ==========================

model = YOLO("yolov8n.pt")

# ==========================
# CAMERA
# ==========================

camera = cv2.VideoCapture(0)

last_detected = None
locked_object = None

# ==========================
# MAIN LOOP
# ==========================

while True:

    success, frame = camera.read()

    if not success:
        break

    results = model(frame)

    # ==========================
    # DETECT OBJECTS
    # ==========================

    best_object = None
    best_confidence = 0

    for result in results:

        for box in result.boxes:

            confidence = float(box.conf[0])

            if confidence > best_confidence:

                class_id = int(box.cls[0])

                best_object = model.names[class_id]
                if model.names[class_id] == "person":
                    continue

                best_confidence = confidence

    if best_object and best_confidence > 0.60:

        last_detected = best_object

    annotated_frame = results[0].plot()

    # ==========================
    # SHOW LOCKED OBJECT
    # ==========================

    if locked_object:

        cv2.putText(
            annotated_frame,
            f"LOCKED: {locked_object}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "Smart Inventory Scanner",
        annotated_frame
    )

    key = cv2.waitKey(1) & 0xFF

    # ==========================
    # L = LOCK OBJECT
    # ==========================

    if key == ord("l"):

        if last_detected:

            locked_object = last_detected

            print(
                f"\nLOCKED OBJECT: {locked_object}"
            )

    # ==========================
    # S = SAVE TO DATABASE
    # ==========================

    if key == ord("s"):

        if not locked_object:
            current_time = time.time()

            if (
                locked_object == last_saved
                and
                current_time - last_saved_time < 5
                ):
                print("Duplicate scan ignored")
            continue

            print(
                "\nNo object locked. Press L first."
            )

        else:

            conn = get_connection()
            cursor = conn.cursor()

            # ==========================
            # FIND PRODUCT USING YOLO MAP
            # ==========================

            cursor.execute("""
            SELECT
            p.product_id,
            p.weight
            FROM yolo_product_mapping y
            JOIN products p
            ON y.product_id = p.product_id
            WHERE LOWER(y.yolo_name)=%s
            """,
            (
                locked_object.lower(),
            ))

            product = cursor.fetchone()

            if not product:

                print(
                    f"\n{locked_object} not mapped to any product."
                )

                conn.close()

            else:

                product_id = product[0]
                weight = product[1]

                # ==========================
                # ASSIGN SHELF
                # ==========================

                shelf_id, shelf_name = assign_shelf(
                    weight
                )

                if not shelf_id:

                    print(
                        "\nNo shelf available."
                    )

                    conn.close()

                else:

                    # ==========================
                    # CHECK EXISTING INVENTORY
                    # ==========================

                    cursor.execute("""
                    SELECT
                        inventory_id,
                        quantity,
                        total_weight
                    FROM inventory
                    WHERE product_id=%s
                    AND shelf_id=%s
                    """,
                    (
                        product_id,
                        shelf_id
                    ))

                    existing = cursor.fetchone()

                    # ==========================
                    # UPDATE INVENTORY
                    # ==========================

                    if existing:

                        inventory_id = existing[0]

                        old_qty = existing[1]

                        old_weight = existing[2]

                        cursor.execute("""
                        UPDATE inventory
                        SET quantity=%s,
                            total_weight=%s
                        WHERE inventory_id=%s   
                        """,
                        (
                            old_qty + 1,
                            old_weight + weight,
                            inventory_id
                        ))

                    else:

                        cursor.execute("""
                        INSERT INTO inventory
                        (
                            product_id,
                            shelf_id,
                            quantity,
                            total_weight
                        )
                        VALUES
                        (%s, %s, %s, %s)
                        """,
                        (
                            product_id,
                            shelf_id,
                            1,
                            weight
                        ))

                  

                    # ==========================
                    # TRANSACTION LOG
                    # ==========================

                    cursor.execute("""
                    INSERT INTO transactions
                    (
                        product_id,
                        action,
                        quantity,
                        shelf_id
                    )
                    VALUES
                    (%s, %s, %s, %s)
                    """,
                    (
                        product_id,
                        "YOLO Scan",
                        1,
                        shelf_id
                    ))

                    # ==========================
                    # MOVEMENT HISTORY
                    # ==========================

                    cursor.execute("""
                    INSERT INTO product_location_history
                    (
                        product_id,
                        shelf_id,
                        quantity
                    )
                    VALUES
                    (%s, %s, %s)
                    """,
                    (
                        product_id,
                        shelf_id,
                        1
                    ))

                    conn.commit()
                    last_saved = locked_object
                    last_saved_time = time.time()
                    locked_object = None
                    print(
                        f"\nSUCCESS: {locked_object}"
                    )

                    print(
                        f"Stored in Shelf: {shelf_name}"
                    )

                    locked_object = None

                    conn.close()

    # ==========================
    # ESC = EXIT
    # ==========================

    if key == 27:
        break


camera.release()
cv2.destroyAllWindows()