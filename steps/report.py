def generate_report(image_name, defects):
    lines = ["="*50, "INSPECTION REPORT", "="*50,
             f"Image: {image_name}", f"Total Defects: {len(defects)}", "-"*50]
    if not defects:
        lines.append("No defects detected.")
        return "\n".join(lines)
    for i, d in enumerate(defects, 1):
        lines += [f"\nDefect #{i}",
                  f"  Type:     {d['type']}",
                  f"  Severity: {d['severity_level']} ({d['severity_score']}/100)",
                  f"  Location: {d.get('location','N/A')}",
                  f"  Coverage: {d.get('size_percent','N/A')}%"]
    return "\n".join(lines)
