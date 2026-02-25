import cv2

COLORS = {"High": (60,60,220), "Medium": (30,145,255), "Low": (50,200,80)}
FONT, FONT_SCALE, THICKNESS = cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1

def draw_annotations(image, defects):
    out = image.copy()
    for idx, d in enumerate(defects, 1):
        x1, y1, x2, y2 = d["bbox"]
        color = COLORS.get(d["severity_level"], (200,200,200))
        cv2.rectangle(out, (x1,y1), (x2,y2), color, 2)
        label = f"#{idx} {d['type']} | {d['severity_level']} ({d['severity_score']})"
        cv2.putText(out, label, (x1+3, max(y1-8,16)),
                    FONT, FONT_SCALE, (240,240,240), THICKNESS, cv2.LINE_AA)
    return out
