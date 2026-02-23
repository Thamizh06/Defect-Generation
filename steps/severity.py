# Severity scoring module
import math

# Weights for the final severity score
W_SIZE     = 0.40
W_LOCATION = 0.35
W_COUNT    = 0.25


def assess_severity(defects, img_w, img_h):
    """Add severity_score, severity_level, location, and size_percent to each defect."""
    total_pixels = img_w * img_h
    num_defects = len(defects)

    scored = []
    for d in defects:
        x1, y1, x2, y2 = d["bbox"]
        area = d["width"] * d["height"]

        # how much of the image does this defect cover
        size_pct = (area / total_pixels) * 100
        size_score = min(100, size_pct * 10)

        cx = (x1 + x2) / 2 #finding the center point
        cy = (y1 + y2) / 2
        dx = abs(cx - img_w / 2) / (img_w / 2)
        dy = abs(cy - img_h / 2) / (img_h / 2)
        dist_from_center = math.sqrt(dx**2 + dy**2) / math.sqrt(2) #Euclidean meathod
        loc_score = (1 - dist_from_center) * 100

        # more defects = bigger problem overall
        cnt_score = min(100, num_defects * 20)

        # combine them
        score = int(size_score * W_SIZE + loc_score * W_LOCATION + cnt_score * W_COUNT)
        score = max(0, min(100, score))

        if score >= 70:
            level = "High"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Low"

        scored.append({
            **d,
            "size_percent": round(size_pct, 2),
            "severity_score": score,
            "severity_level": level,
            "location": _where_in_image(cx, cy, img_w, img_h),
        })

    return scored


def _where_in_image(cx, cy, w, h):
    """Map the defect center to a 3x3 grid label (e.g. Top-Left, Center, Bottom)."""
    nx = cx / w  # normalized x (0.0 = left, 1.0 = right)
    ny = cy / h

    center_min = 0.44
    center_max = 0.56

    if center_min <= nx <= center_max:
        col = "Center"
    elif nx < center_min:
        col = "Left"
    else:
        col = "Right"

    if center_min <= ny <= center_max:
        row = "Middle"
    elif ny < center_min:
        row = "Top"
    elif ny > center_max:
        row = "Bottom"
    else:
        row = "Middle"

    if row == "Middle" and col == "Center":
        return "Center"
    elif row == "Middle":
        return col
    elif col == "Center":
        return row
    else:
        return f"{row}-{col}"
