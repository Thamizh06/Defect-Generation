KNOWN_DEFECTS = {
    "Crack":   {"causes": ["Material fatigue", "Impact damage"],
                "risks":   ["Crack may spread"], "actions": ["Measure depth", "Replace if critical"]},
    "Scratch": {"causes": ["Friction during handling", "Tool marks"],
                "risks":   ["Possible stress point"], "actions": ["Polish surface", "Review handling"]},
    "Rust":    {"causes": ["Moisture exposure", "Coating damage"],
                "risks":   ["Material weakens over time"], "actions": ["Remove rust", "Fix moisture source"]},
}
DEFAULT_REASONING = {
    "causes":  ["Manufacturing defect", "Wear and tear"],
    "risks":   ["Quality issue requiring inspection"],
    "actions": ["Inspect further", "Document and report"],
}

def reason_root_causes(defects):
    return _use_rules(defects), "No Gemini key. Using rule-based fallback."

def _use_rules(defects):
    for d in defects:
        r = KNOWN_DEFECTS.get(d["type"], DEFAULT_REASONING)
        d["causes"]  = r["causes"]
        d["risks"]   = r["risks"]
        d["actions"] = r["actions"]
        d["reasoning_source"] = "Rule-based"
    return defects
