
import os, sys

from run import example_theory

USAGE = '\n\tpython3 test.py [draft|final]\n'
EXPECTED_VAR_MIN = 10
EXPECTED_CONS_MIN = 50

def test_theory():
    T = example_theory()

    assert len(T.vars()) > EXPECTED_VAR_MIN, "Only %d variables -- your theory is likely not sophisticated enough for the course project." % len(T.vars())
    assert T.size() > EXPECTED_CONS_MIN, "Only %d operators in the formula -- your theory is likely not sophisticated enough for the course project." % T.size()
    assert not T.valid(), "Theory is valid (every assignment is a solution). Something is likely wrong with the constraints."
    assert not T.negate().valid(), "Theory is inconsistent (no solutions exist). Something is likely wrong with the constraints."

def file_checks(stage):
    proofs_jp = os.path.isfile(os.path.join('.','documents',stage,'proofs.jp'))
    modelling_report_docx = os.path.isfile(os.path.join('.','documents',stage,'modelling_report.docx'))
    modelling_report_pptx = os.path.isfile(os.path.join('.','documents',stage,'modelling_report.pptx'))
    report_txt = os.path.isfile(os.path.join('.','documents',stage,'report.txt'))
    report_pdf = os.path.isfile(os.path.join('.','documents',stage,'report.pdf'))

    assert proofs_jp, "Missing proofs.jp in your %s folder." % stage
    assert modelling_report_docx or modelling_report_pptx or (report_txt and report_pdf), \
            "Missing your report (Word, PowerPoint, or OverLeaf) in your %s folder" % stage

def test_draft_files():
    file_checks('draft')

def test_final_files():
    file_checks('final')

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['draft', 'final']:
        print(USAGE)
        exit(1)
    test_theory()
    file_checks(sys.argv[1])
