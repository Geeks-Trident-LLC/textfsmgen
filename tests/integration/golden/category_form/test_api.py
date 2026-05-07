def test_golden(golden_case, run_golden_test):
    kind, case = golden_case
    run_golden_test(kind, case)
