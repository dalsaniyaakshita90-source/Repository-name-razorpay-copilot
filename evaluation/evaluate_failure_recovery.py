import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCEPTIONS = ROOT / "frontend" / "public" / "exceptions.csv"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_payment(rows, payment_id):
    return [
        row for row in rows
        if row.get("payment_id", "").upper() == payment_id.upper()
    ]


def judge_evidence(rows, payment_id):
    matches = find_payment(rows, payment_id)

    if not matches:
        return "UNRESOLVED"

    required = [
        "payment_id",
        "exception_type",
        "severity",
        "reason",
        "evidence",
    ]

    if all(all(row.get(field, "").strip() for field in required)
           for row in matches):
        return "VERIFIED"

    return "PARTIAL"


def main():
    rows = load_csv(EXCEPTIONS)

    tests = []

    # Fully supported real evidence
    tests.append((
        "PAY_0041",
        rows,
        "VERIFIED"
    ))

    # Unknown payment
    tests.append((
        "PAY_9999",
        rows,
        "UNRESOLVED"
    ))

    # Synthetic partial-evidence case
    partial_rows = [{
        "payment_id": "PAY_PARTIAL",
        "exception_type": "AMOUNT_MISMATCH",
        "severity": "HIGH",
        "reason": "Ledger and bank amounts differ.",
        "evidence": ""
    }]

    tests.append((
        "PAY_PARTIAL",
        partial_rows,
        "PARTIAL"
    ))

    passed = 0

    print()
    print("=" * 64)
    print("RAZORPAY COPILOT - FAILURE RECOVERY EVALUATION")
    print("=" * 64)
    print()

    for payment_id, source_rows, expected in tests:
        actual = judge_evidence(source_rows, payment_id)

        if actual == expected:
            passed += 1
            result = "PASS"
        else:
            result = "FAIL"

        print(
            f"{payment_id:<15} "
            f"expected={expected:<12} "
            f"actual={actual:<12} "
            f"{result}"
        )

    print()
    print("-" * 64)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Failure-recovery accuracy: {passed / len(tests) * 100:.2f}%")
    print()

    print("RECOVERY POLICY")
    print("-" * 64)
    print("VERIFIED  -> complete supporting evidence")
    print("PARTIAL   -> matching evidence exists but is incomplete")
    print("UNRESOLVED -> no matching evidence exists")
    print("No missing evidence may be silently invented.")
    print()
    print("=" * 64)


if __name__ == "__main__":
    main()
