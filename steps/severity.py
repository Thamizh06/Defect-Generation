import math

W_SIZE     = 0.40
W_LOCATION = 0.35
W_COUNT    = 0.25

def assess_severity(defects, img_w, img_h):
    total_pixels = img_w * img_h
    num_defects  = len(defects)
    scored = []
    for d in defects:
        x1, y1, x2, y2 = d["bbox"]
        area       = d["width"] * d["height"]
        size_pct   = (area / total_pixels) * 100
        size_score = min(100, size_pct * 10)
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        dx = abs(cx - img_w / 2) / (img_w / 2)
        dy = abs(cy - img_h / 2) / (img_h / 2)
        dist_from_center = math.sqrt(dx**2 + dy**2) / math.sqrt(2)
        loc_score  = (1 - dist_from_center) * 100
        cnt_score  = min(100, num_defects * 20)
        score = int(size_score * W_SIZE + loc_score * W_LOCATION + cnt_score * W_COUNT)
        score = max(0, min(100, score))
        level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
        scored.append({**d, "size_percent": round(size_pct, 2),
                       "severity_score": score, "severity_level": level,
                       "location": _where_in_image(cx, cy, img_w, img_h)})
    return scored

def _where_in_image(cx, cy, w, h):
    nx, ny = cx / w, cy / h
    center_min, center_max = 0.44, 0.56
    col = "Center" if center_min <= nx <= center_max else ("Left" if nx < center_min else "Right")
    row = "Middle" if center_min <= ny <= center_max else ("Top"  if ny < center_min else "Bottom")
    if row == "Middle" and col == "Center": return "Center"
    elif row == "Middle": return col
    elif col == "Center": return row
    else: return f"{row}-{col}"
