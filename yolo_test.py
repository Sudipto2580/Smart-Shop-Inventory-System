from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

camera = cv2.VideoCapture(0)

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

            print(
                f"{name} : {confidence:.2f}"
            )

    annotated_frame = results[0].plot()

    cv2.imshow(
        "YOLO Detection",
        annotated_frame
    )

    if cv2.waitKey(1) == 27:
        break

camera.release()
cv2.destroyAllWindows()