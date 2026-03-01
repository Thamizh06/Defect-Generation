# pipeline.py
# Central import hub — all pipeline steps are imported here
# so that app.py only needs one import line.

from steps.detection import detect_defects
from steps.severity import assess_severity
from steps.reasoning import reason_root_causes
from steps.annotation import draw_annotations
from steps.report import generate_report, generate_pdf_report
