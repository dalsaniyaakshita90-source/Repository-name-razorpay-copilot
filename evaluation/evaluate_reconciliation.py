import csv
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH = ROOT / "data" / "ground_truth" / "injected_incidents.csv"
EXCEPTIONS = ROOT / "frontend" / "public" / "exceptions.csv"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    if not GROUND_TRUTH.exists():
        print(f"ERROR: Ground truth not found: {GROUND_TRUTH}")
        return

    if not EXCEPTIONS.exists():
        print(f"ERROR: Exceptions file not found: {EXCEPTIONS}")
        return

    truth = load_csv(GROUND_TRUTH)
    detected = load_csv(EXCEPTIONS)

    truth_map = {
        row["payment_id"]: row["exception_type"]
        for row in truth
        if row.get("payment_id")
    }

    detected_map = {
        row["payment_id"]: row["exception_type"]
        for row in detected
        if row.get("payment_id")
    }

    truth_ids = set(truth_map)
    detected_ids = set(detected_map)

    true_positives = truth_ids & detected_ids
    missed = truth_ids - detected_ids
    false_positives = detected_ids - truth_ids

    correctly_classified = {
        payment_id
        for payment_id in true_positives
        if truth_map[payment_id] == detected_map[payment_id]
    }

    misclassified = {
        payment_id
        for payment_id in true_positives
        if truth_map[payment_id] != detected_map[payment_id]
    }

    detection_rate = (
        len(true_positives) / len(truth_ids) * 100
        if truth_ids else 0
    )

    classification_rate = (
        len(correctly_classified) / len(truth_ids) * 100
        if truth_ids else 0
    )

    print()
    print("=" * 55)
    print("RAZORPAY COPILOT - RECONCILIATION EVALUATION")
    print("=" * 55)
    print()
    print(f"Ground-truth incidents : {len(truth_ids)}")
    print(f"Detected exceptions    : {len(detected_ids)}")
    print(f"True positives         : {len(true_positives)}")
    print(f"Missed incidents       : {len(missed)}")
    print(f"False positives        : {len(false_positives)}")
    print(f"Detection rate         : {detection_rate:.2f}%")
    print(f"Classification rate    : {classification_rate:.2f}%")
    print()

    if misclassified:
        print("MISCLASSIFIED INCIDENTS:")
        for payment_id in sorted(misclassified):
            print(
                f"  - {payment_id}: "
                f"expected={truth_map[payment_id]}, "
                f"detected={detected_map[payment_id]}"
            )
        print()

    if missed:
        print("MISSED INCIDENTS:")
        for payment_id in sorted(missed):
            print(f"  - {payment_id}")
        print()

    if false_positives:
        print("FALSE POSITIVES:")
        for payment_id in sorted(false_positives):
            print(f"  - {payment_id}")
        print()

    print("CLASSIFICATION BREAKDOWN")
    print("-" * 55)

    expected_counts = Counter(truth_map.values())
    detected_counts = Counter(
        detected_map[payment_id]
        for payment_id in true_positives
    )

    for issue in sorted(expected_counts):
        print(
            f"{issue:<25} "
            f"expected={expected_counts[issue]:<3} "
            f"detected={detected_counts[issue]:<3}"
        )

    print()
    print("=" * 55)


if __name__ == "__main__":
    main()
