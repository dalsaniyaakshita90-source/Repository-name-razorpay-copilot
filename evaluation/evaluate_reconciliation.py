import csv
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH = ROOT / "data" / "ground_truth" / "injected_incidents.csv"
EXCEPTIONS = ROOT / "frontend" / "public" / "exceptions.csv"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_exception_map(rows):
    result = defaultdict(set)

    for row in rows:
        payment_id = row.get("payment_id")
        exception_type = row.get("exception_type")

        if payment_id and exception_type:
            result[payment_id].add(exception_type)

    return dict(result)


def main():
    if not GROUND_TRUTH.exists():
        print(f"ERROR: Ground truth not found: {GROUND_TRUTH}")
        return

    if not EXCEPTIONS.exists():
        print(f"ERROR: Exceptions file not found: {EXCEPTIONS}")
        return

    truth = load_csv(GROUND_TRUTH)
    detected = load_csv(EXCEPTIONS)

    truth_map = build_exception_map(truth)
    detected_map = build_exception_map(detected)

    truth_ids = set(truth_map)
    detected_ids = set(detected_map)

    true_positives = truth_ids & detected_ids
    missed = truth_ids - detected_ids
    false_positives = detected_ids - truth_ids

    correctly_classified = {
        payment_id
        for payment_id in true_positives
        if truth_map[payment_id].issubset(detected_map[payment_id])
    }

    misclassified = {
        payment_id
        for payment_id in true_positives
        if not truth_map[payment_id].issubset(detected_map[payment_id])
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
    print("=" * 60)
    print("RAZORPAY COPILOT - RECONCILIATION EVALUATION")
    print("=" * 60)
    print()

    print(f"Ground-truth incidents : {len(truth_ids)}")
    print(f"Detected exceptions    : {len(detected)}")
    print(f"Detected payments      : {len(detected_ids)}")
    print(f"True positive payments : {len(true_positives)}")
    print(f"Missed incidents       : {len(missed)}")
    print(f"False positive payments: {len(false_positives)}")
    print(f"Detection rate         : {detection_rate:.2f}%")
    print(f"Classification rate    : {classification_rate:.2f}%")
    print()

    if misclassified:
        print("MISCLASSIFIED INCIDENTS:")
        for payment_id in sorted(misclassified):
            print(
                f"  - {payment_id}: "
                f"expected={sorted(truth_map[payment_id])}, "
                f"detected={sorted(detected_map[payment_id])}"
            )
        print()

    if missed:
        print("MISSED INCIDENTS:")
        for payment_id in sorted(missed):
            print(f"  - {payment_id}")
        print()

    if false_positives:
        print("FALSE POSITIVE PAYMENTS:")
        for payment_id in sorted(false_positives):
            print(f"  - {payment_id}")
        print()

    print("CLASSIFICATION BREAKDOWN")
    print("-" * 60)

    expected_counts = Counter()

    for exception_types in truth_map.values():
        for issue in exception_types:
            expected_counts[issue] += 1

    detected_counts = Counter()

    for payment_id in true_positives:
        for issue in detected_map[payment_id]:
            if issue in truth_map[payment_id]:
                detected_counts[issue] += 1

    for issue in sorted(expected_counts):
        print(
            f"{issue:<25} "
            f"expected={expected_counts[issue]:<3} "
            f"detected={detected_counts[issue]:<3}"
        )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()