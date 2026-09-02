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


def classify_payment(rows, payment_id):
    matches = find_payment(rows, payment_id)

    if not matches:
        return {
            "status": "UNRESOLVED",
            "evidence": False,
            "reason": "No matching reconciliation evidence was found."
        }

    evidence_complete = all(
        row.get("payment_id")
        and row.get("exception_type")
        and row.get("severity")
        and row.get("reason")
        and row.get("evidence")
        for row in matches
    )

    if not evidence_complete:
        return {
            "status": "UNRESOLVED",
            "evidence": False,
            "reason": "A matching exception exists, but its supporting evidence is incomplete."
        }

    return {
        "status": "VERIFIED",
        "evidence": True,
        "reason": "Matching exception evidence is present."
    }


def main():

    if not EXCEPTIONS.exists():
        print(f"ERROR: Exceptions file not found: {EXCEPTIONS}")
        return

    rows = load_csv(EXCEPTIONS)

    tests = [
        ("PAY_0047", "VERIFIED"),
        ("PAY_0048", "VERIFIED"),
        ("PAY_9999", "UNRESOLVED"),
    ]

    passed = 0

    print()
    print("=" * 60)
    print("RAZORPAY COPILOT - AI JUDGMENT EVALUATION")
    print("=" * 60)
    print()

    print(f"Evidence records loaded : {len(rows)}")
    print()

    for payment_id, expected in tests:

        result = classify_payment(rows, payment_id)

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

        print(
            f"  Evidence present: {result['evidence']}"
        )

        print(
            f"  Reason: {result['reason']}"
        )

        print()

    print("-" * 60)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(
        f"Judgment accuracy: "
        f"{passed / len(tests) * 100:.2f}%"
    )

    print()
    print("EVIDENCE POLICY")
    print("-" * 60)
    print("VERIFIED requires matching supporting evidence.")
    print("Unknown payments must return UNRESOLVED.")
    print("Missing evidence must never produce VERIFIED.")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
