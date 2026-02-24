import os
import json

GEMINI_MODEL = "gemini-2.5-flash"

# Rule-based fallback: predefined causes, risks, and actions per defect type
KNOWN_DEFECTS = {
    "Crack": {
        "causes": ["Material fatigue or stress", "Impact damage"],
        "risks": ["Crack may spread and cause failure"],
        "actions": ["Measure crack depth", "Replace if critical"],
    },
    "Scratch": {
        "causes": ["Friction during handling", "Tool marks"],
        "risks": ["Cosmetic issue, possible stress point"],
        "actions": ["Polish surface", "Review handling process"],
    },
    "Rust": {
        "causes": ["Moisture exposure", "Coating damage"],
        "risks": ["Material will weaken over time"],
        "actions": ["Remove rust and apply coating", "Fix moisture source"],
    },
}

DEFAULT_REASONING = {
    "causes": ["Manufacturing defect", "Wear and tear"],
    "risks": ["Quality issue requiring inspection"],
    "actions": ["Inspect further", "Document and report"],
}


def reason_root_causes(defects):
    """Analyze defects using Gemini AI. Returns (defects, error_message).
    error_message is None if Gemini worked, otherwise contains fallback info."""
    api_key = os.getenv("GEMINI_API_KEY", "")

    if api_key:
        return _ask_gemini(defects, api_key)
    return _use_rules(defects), "No Gemini API key found. Using rule-based fallback."


def _ask_gemini(defects, api_key):
    """Call Gemini API for root cause analysis."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        # build a clean summary to send (no image data, just text)
        summary = []
        for d in defects:
            summary.append({
                "defect_type": d["type"],
                "severity": d["severity_level"],
                "size_percent": d["size_percent"],
                "location": d["location"],
            })

        prompt = f"""You are an industrial quality inspector AI.
Analyze these defects detected by computer vision and provide root cause analysis.

Defect Data:
{json.dumps(summary, indent=2)}

For EACH defect, provide:
1. Possible Causes (2 bullet points)
2. Risks (1 bullet point)
3. Recommended Actions (2 bullet points)

Respond in JSON format as a list of objects with keys:
defect_type, causes, risks, actions (each is a list of strings)"""

        resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)

        # gemini sometimes wraps json in markdown code blocks, strip that
        text = resp.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(text)

        for i, d in enumerate(defects):
            if i < len(parsed):
                r = parsed[i]
                d["causes"] = r.get("causes", ["Unknown"])
                d["risks"] = r.get("risks", ["Further assessment needed"])
                d["actions"] = r.get("actions", ["Inspect further"])
            else:
                _apply_rule(d)
            d["reasoning_source"] = "Gemini AI"

        return defects, None 

    except Exception as e:
        err_msg = str(e)
        print(f"Gemini failed: {err_msg} - falling back to rules")
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            reason = "Gemini API quota exceeded. Using rule-based fallback. Try again tomorrow."
        else:
            reason = f"Gemini API error: {err_msg}. Using rule-based fallback."
        return _use_rules(defects), reason


def _use_rules(defects):
    """Apply rule-based reasoning to all defects."""
    for d in defects:
        _apply_rule(d)
        d["reasoning_source"] = "Rule-based"
    return defects


def _apply_rule(defect):
    """Set causes/risks/actions from the KNOWN_DEFECTS dictionary."""
    r = KNOWN_DEFECTS.get(defect["type"], DEFAULT_REASONING)
    defect["causes"] = r["causes"]
    defect["risks"] = r["risks"]
    defect["actions"] = r["actions"]
