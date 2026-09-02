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
# 1. MISSING BANK
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

    # Duplicate payments are handled separately.
    if len(bank_by_id[payment_id]) > 1:
        continue

    ledger_amount = round(
        float(ledger_row["amount"]),
        2
    )

    bank_amount = round(
        float(bank_by_id[payment_id][0]["credit_amount"]),
        2
    )

    difference = round(
        ledger_amount - bank_amount,
        2
    )

    if abs(difference) > 0.01:

        # Check whether Razorpay also disagrees.
        razorpay_conflict = False

        if payment_id in razorpay_by_id:

            razorpay_gross = round(
                float(
                    razorpay_by_id[payment_id]["gross_amount"]
                ),
                2
            )

            razorpay_conflict = (
                abs(ledger_amount - razorpay_gross) > 0.01
            )

        # If Razorpay also conflicts with the ledger,
        # leave this payment for UNRESOLVED_DIFFERENCE.
        if not razorpay_conflict:

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
# 3. DATE VARIANCE
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
# 4. DUPLICATE
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
# 5. REFUND DIFFERENCE
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
                f"Refund amount: Rs {amount:.2f}"
            )


# ============================================================
# 6. FEE / TAX MISMATCH
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
# 7. SOURCE CONFLICT
# ============================================================

for payment_id, ledger_row in ledger_by_id.items():

    if payment_id not in bank_by_id:
        continue

    if payment_id not in razorpay_by_id:
        continue

    # Duplicate records are handled separately.
    if len(bank_by_id[payment_id]) > 1:
        continue

    ledger_amount = round(
        float(ledger_row["amount"]),
        2
    )

    bank_amount = round(
        float(bank_by_id[payment_id][0]["credit_amount"]),
        2
    )

    razorpay_gross = round(
        float(
            razorpay_by_id[payment_id]["gross_amount"]
        ),
        2
    )

    # Ledger and bank agree,
    # but Razorpay disagrees.

    if (
        abs(ledger_amount - bank_amount) <= 0.01
        and
        abs(ledger_amount - razorpay_gross) > 0.01
    ):

        add_exception(
            payment_id,
            "SOURCE_CONFLICT",
            "HIGH",
            "Bank and ledger agree, but Razorpay gross amount conflicts with both sources.",
            (
                f"Ledger: Rs {ledger_amount:.2f}; "
                f"Bank: Rs {bank_amount:.2f}; "
                f"Razorpay gross: Rs {razorpay_gross:.2f}"
            )
        )


# ============================================================
# 8. UNRESOLVED DIFFERENCE
# ============================================================

for payment_id, ledger_row in ledger_by_id.items():

    if payment_id not in bank_by_id:
        continue

    if payment_id not in razorpay_by_id:
        continue

    # Duplicate records are handled separately.
    if len(bank_by_id[payment_id]) > 1:
        continue

    ledger_amount = round(
        float(ledger_row["amount"]),
        2
    )

    bank_amount = round(
        float(bank_by_id[payment_id][0]["credit_amount"]),
        2
    )

    razorpay_row = razorpay_by_id[payment_id]

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

    bank_difference = round(
        ledger_amount - bank_amount,
        2
    )

    razorpay_difference = round(
        net - expected_net,
        2
    )

    # UNRESOLVED means:
    # 1. Ledger and bank disagree
    # 2. Razorpay also conflicts with the ledger
    # 3. Razorpay's own net calculation is internally valid
    #
    # This distinguishes it from:
    # AMOUNT_MISMATCH
    # FEE_TAX_MISMATCH
    # SOURCE_CONFLICT

    razorpay_source_conflict = (
        abs(ledger_amount - gross) > 0.01
    )

    if (
        abs(bank_difference) > 0.01
        and
        razorpay_source_conflict
        and
        abs(razorpay_difference) <= 0.01
    ):

        add_exception(
            payment_id,
            "UNRESOLVED_DIFFERENCE",
            "HIGH",
            "Ledger, bank and Razorpay sources disagree, and the available records do not establish a single reconciled explanation.",
            (
                f"Ledger: Rs {ledger_amount:.2f}; "
                f"Bank: Rs {bank_amount:.2f}; "
                f"Bank difference: Rs {bank_difference:.2f}; "
                f"Razorpay gross: Rs {gross:.2f}; "
                f"Razorpay reported net: Rs {net:.2f}; "
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
