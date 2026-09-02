import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime


BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "raw"
OUTPUT = BASE / "data" / "processed" / "exceptions.csv"


def load_csv(filename):
    with open(DATA / filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


ledger = load_csv("ledger.csv")
bank = load_csv("bank.csv")
razorpay = load_csv("razorpay.csv")
adjustments = load_csv("adjustments.csv")


ledger_by_id = {
    row["payment_id"]: row
    for row in ledger
}

bank_by_id = defaultdict(list)

for row in bank:
    bank_by_id[row["payment_id"]].append(row)

razorpay_by_id = {
    row["payment_id"]: row
    for row in razorpay
}

adjustments_by_id = defaultdict(list)

for row in adjustments:
    adjustments_by_id[row["payment_id"]].append(row)


exceptions = []


def add_exception(payment_id, issue, severity, reason, evidence):
    exceptions.append({
        "payment_id": payment_id,
        "exception_type": issue,
        "severity": severity,
        "reason": reason,
        "evidence": evidence
    })


# ============================================================
# 1. MISSING BANK RECORD
# ============================================================

for payment_id, ledger_row in ledger_by_id.items():

    if ledger_row["status"].upper() != "SUCCESS":
        continue

    if payment_id not in bank_by_id:

        add_exception(
            payment_id,
            "MISSING_BANK",
            "HIGH",
            "Successful ledger transaction has no matching bank record.",
            f"Ledger amount: Rs {float(ledger_row['amount']):.2f}"
        )


# ============================================================
# 2. AMOUNT MISMATCH
# ============================================================

for payment_id, ledger_row in ledger_by_id.items():

    if payment_id not in bank_by_id:
        continue

    ledger_amount = round(
        float(ledger_row["amount"]),
        2
    )

    bank_amount = round(
        sum(
            float(row["credit_amount"])
            for row in bank_by_id[payment_id]
        ),
        2
    )

    difference = round(
        ledger_amount - bank_amount,
        2
    )

    if abs(difference) > 0.01:

        add_exception(
            payment_id,
            "AMOUNT_MISMATCH",
            "HIGH",
            "Ledger amount does not match bank credit.",
            (
                f"Ledger: Rs {ledger_amount:.2f}; "
                f"Bank: Rs {bank_amount:.2f}; "
                f"Difference: Rs {difference:.2f}"
            )
        )


# ============================================================
# 3. SETTLEMENT DATE VARIANCE
# ============================================================

for payment_id, ledger_row in ledger_by_id.items():

    if payment_id not in razorpay_by_id:
        continue

    ledger_date = ledger_row["transaction_date"]
    settlement_date = razorpay_by_id[payment_id]["settlement_date"]

    try:
        d1 = datetime.strptime(
            ledger_date,
            "%Y-%m-%d"
        )

        d2 = datetime.strptime(
            settlement_date,
            "%Y-%m-%d"
        )

        days = (d2 - d1).days

    except ValueError:
        continue

    # Normal settlement can take a few days.
    # Flag unusually large variance.

    if days > 3 or days < 0:

        add_exception(
            payment_id,
            "DATE_VARIANCE",
            "MEDIUM",
            "Settlement date differs significantly from transaction date.",
            (
                f"Transaction date: {ledger_date}; "
                f"Settlement date: {settlement_date}; "
                f"Variance: {days} day(s)"
            )
        )


# ============================================================
# 4. DUPLICATE BANK RECORD
# ============================================================

for payment_id, rows in bank_by_id.items():

    if len(rows) > 1:

        total = round(
            sum(
                float(row["credit_amount"])
                for row in rows
            ),
            2
        )

        add_exception(
            payment_id,
            "DUPLICATE",
            "HIGH",
            "Multiple bank records exist for the same payment.",
            (
                f"Bank records: {len(rows)}; "
                f"Combined credit: Rs {total:.2f}"
            )
        )


# ============================================================
# 5. REFUND / ADJUSTMENT
# ============================================================

for payment_id, rows in adjustments_by_id.items():

    for row in rows:

        adjustment_type = row.get(
            "type",
            ""
        ).upper()

        amount = float(
            row.get(
                "amount",
                0
            ) or 0
        )

        if adjustment_type == "REFUND":

            add_exception(
                payment_id,
                "REFUND_DIFFERENCE",
                "MEDIUM",
                "Refund adjustment requires reconciliation.",
                (
                    f"Refund amount: Rs {amount:.2f}"
                )
            )


# ============================================================
# 6. FEE / TAX CHECK
# ============================================================

for payment_id, razorpay_row in razorpay_by_id.items():

    if payment_id not in ledger_by_id:
        continue

    gross = round(
        float(razorpay_row["gross_amount"]),
        2
    )

    fee = round(
        float(razorpay_row["fee"]),
        2
    )

    tax = round(
        float(razorpay_row["tax"]),
        2
    )

    net = round(
        float(razorpay_row["net_amount"]),
        2
    )

    expected_net = round(
        gross - fee - tax,
        2
    )

    difference = round(
        net - expected_net,
        2
    )

    if abs(difference) > 0.01:

        add_exception(
            payment_id,
            "FEE_TAX_MISMATCH",
            "MEDIUM",
            "Razorpay net amount does not reconcile with gross amount, fee and tax.",
            (
                f"Gross: Rs {gross:.2f}; "
                f"Fee: Rs {fee:.2f}; "
                f"Tax: Rs {tax:.2f}; "
                f"Reported net: Rs {net:.2f}; "
                f"Expected net: Rs {expected_net:.2f}"
            )
        )


# ============================================================
# SAVE RESULTS
# ============================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    OUTPUT,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "payment_id",
            "exception_type",
            "severity",
            "reason",
            "evidence"
        ]
    )

    writer.writeheader()
    writer.writerows(exceptions)


# ============================================================
# SUMMARY
# ============================================================

counts = defaultdict(int)

for exception in exceptions:
    counts[
        exception["exception_type"]
    ] += 1


print()
print("RAZORPAY COPILOT - RECONCILIATION")
print("=" * 45)

print(
    f"Ledger records:      {len(ledger)}"
)

print(
    f"Bank records:        {len(bank)}"
)

print(
    f"Razorpay records:    {len(razorpay)}"
)

print(
    f"Adjustments:         {len(adjustments)}"
)

print()
print(
    f"Exceptions detected: {len(exceptions)}"
)

print()
print("EXCEPTION BREAKDOWN")
print("-" * 45)

for issue, count in sorted(counts.items()):
    print(
        f"{issue:<25} {count}"
    )

print()
print(
    f"Saved to: {OUTPUT}"
)
