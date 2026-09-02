import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCEPTIONS = ROOT / "frontend" / "public" / "exceptions.csv"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_payment(rows, payment_id):
    return [
        row
        for row in rows
        if row.get("payment_id", "").upper() == payment_id.upper()
    ]


def verify_evidence(rows, payment_id):
    matches = find_payment(rows, payment_id)

    if not matches:
        return {
            "status": "UNRESOLVED",
            "evidence": False,
            "reason": "No matching reconciliation evidence was found."
        }

    required_fields = [
        "payment_id",
        "exception_type",
        "severity",
        "reason",
        "evidence",
    ]

    complete = all(
        all(row.get(field, "").strip() for field in required_fields)
        for row in matches
    )

    if not complete:
        return {
            "status": "UNRESOLVED",
            "evidence": False,
            "reason": "A matching exception exists, but its supporting evidence is incomplete."
        }

    return {
        "status": "VERIFIED",
        "evidence": True,
        "reason": "The reconciliation evidence supports the exception."
    }


def main():
    if not EXCEPTIONS.exists():
        print(f"ERROR: Exceptions file not found: {EXCEPTIONS}")
        return

    rows = load_csv(EXCEPTIONS)

    tests = [
        ("PAY_0041", "VERIFIED"),
        ("PAY_0047", "VERIFIED"),
        ("PAY_0048", "VERIFIED"),
        ("PAY_9999", "UNRESOLVED"),
    ]

    passed = 0

    print()
    print("=" * 64)
    print("RAZORPAY COPILOT - AI JUDGMENT EVALUATION")
    print("=" * 64)
    print()
    print(f"Evidence records loaded : {len(rows)}")
    print()

    for payment_id, expected in tests:
        result = verify_evidence(rows, payment_id)
        actual = result["status"]

        if actual == expected:
            passed += 1
            outcome = "PASS"
        else:
            outcome = "FAIL"

        print(
            f"{payment_id:<12} "
            f"expected={expected:<12} "
            f"actual={actual:<12} "
            f"{outcome}"
        )
        print(f"  Evidence supported: {result['evidence']}")
        print(f"  Judgment: {result['reason']}")
        print()

    print("-" * 64)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Judgment accuracy: {passed / len(tests) * 100:.2f}%")
    print()

    print("JUDGMENT POLICY")
    print("-" * 64)
    print("VERIFIED = evidence supports the claim.")
    print("UNRESOLVED = evidence is absent or insufficient.")
    print("A business exception may remain OPEN even when its evidence is VERIFIED.")
    print("The Copilot must never invent missing evidence.")
    print()

    print("=" * 64)


if __name__ == "__main__":
    main()
