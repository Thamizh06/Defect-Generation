import cv2

# Colors per severity level (BGR format — OpenCV uses BGR, not RGB)
COLORS = {
    "High":   (60,  60,  220),   # red
    "Medium": (30,  145, 255),   # orange
    "Low":    (50,  200, 80),    # green
}

FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.42
THICKNESS  = 1


def draw_annotations(image, defects):
    """Return a copy of the image with bounding boxes, and labels."""
    out = image.copy()

    for idx, d in enumerate(defects, 1):
        x1, y1, x2, y2 = d["bbox"]
        color = COLORS.get(d["severity_level"], (200, 200, 200))

        # Bounding box around the defect
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        # Label above the box: index, defect type, severity, score
        label = f"#{idx} {d['type']} | {d['severity_level']} ({d['severity_score']})"
        (text_w, text_h), _ = cv2.getTextSize(label, FONT, FONT_SCALE, THICKNESS)

        # dark background behind the label so it's readable on any image
        label_y = max(y1 - 8, text_h + 8)
        cv2.rectangle(out,
                      (x1, label_y - text_h - 4),
                      (x1 + text_w + 6, label_y + 4),
                      (20, 20, 20), cv2.FILLED)

        cv2.putText(out, label, (x1 + 3, label_y),
                    FONT, FONT_SCALE, (240, 240, 240), THICKNESS, cv2.LINE_AA)

    return out
