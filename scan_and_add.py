from ultralytics import YOLO
import cv2

from database import get_connection
from allocation import assign_shelf

model = YOLO("yolov8n.pt")

camera = cv2.VideoCapture(0)

last_detected = None
locked_object = None

while True:

    success, frame = camera.read()

    if not success:
        break

    results = model(frame)

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            name = model.names[class_id]

            confidence = float(box.conf[0])

            if confidence > 0.60:

                last_detected = name

    annotated_frame = results[0].plot()

    # Show currently locked object on screen
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
        "Scan Product",
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
                f"LOCKED: {locked_object}"
            )

    # ==========================
    # S = SAVE LOCKED OBJECT
    # ==========================

    if key == ord("s"):

        if locked_object:

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            SELECT product_id,
                   weight
            FROM products
            WHERE LOWER(product_name)=?
            """,
            (
                locked_object.lower(),
            ))

            product = cursor.fetchone()

            if product:

                product_id = product[0]
                weight = product[1]

                shelf_id, shelf_name = assign_shelf(
                    weight
                )

                if shelf_id:

                    cursor.execute("""
                    INSERT INTO inventory
                    (
                    product_id,
                    shelf_id,
                    quantity,
                    total_weight
                    )
                    VALUES
                    (?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        shelf_id,
                        1,
                        weight
                    ))

                    cursor.execute("""
                    INSERT INTO transactions
                    (
                    product_id,
                    action,
                    quantity,
                    shelf_id
                    )
                    VALUES
                    (?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        "YOLO Scan",
                        1,
                        shelf_id
                    ))

                    cursor.execute("""
                    UPDATE shelves
                    SET used_capacity =
                    used_capacity + ?
                    WHERE shelf_id = ?
                    """,
                    (
                        weight,
                        shelf_id
                    ))

                    conn.commit()

                    print(
                        f"{locked_object} stored in {shelf_name}"
                    )

                    # Reset lock after saving
                    locked_object = None

                else:

                    print(
                        "No shelf available"
                    )

            else:

                print(
                    f"{locked_object} not found in Product Master"
                )

            conn.close()

        else:

            print(
                "No object locked. Press L first."
            )

    # ==========================
    # ESC = EXIT
    # ==========================

    if key == 27:
        break

camera.release()
cv2.destroyAllWindows()