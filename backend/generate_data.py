import csv
from datetime import date, timedelta
from pathlib import Path


START = date(2026, 8, 1)

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
GROUND_TRUTH = BASE / "data" / "ground_truth" / "injected_incidents.csv"


transactions = []


# ============================================================
# 40 NORMAL TRANSACTIONS
# ============================================================

for i in range(1, 41):

    amount = 1500 + ((i * 731) % 6500)

    transactions.append(
        (
            f"PAY_{i:04d}",
            amount,
            "MATCHED"
        )
    )


# ============================================================
# 16 CONTROLLED INCIDENTS
# ============================================================

transactions.extend([
    ("PAY_0041", 5000, "AMOUNT_MISMATCH"),
    ("PAY_0042", 6400, "DATE_VARIANCE"),
    ("PAY_0043", 2800, "MISSING_BANK"),
    ("PAY_0044", 3600, "DUPLICATE"),
    ("PAY_0045", 4500, "REFUND_DIFFERENCE"),
    ("PAY_0046", 5200, "FEE_TAX_MISMATCH"),
    ("PAY_0047", 6100, "SOURCE_CONFLICT"),
    ("PAY_0048", 7300, "UNRESOLVED_DIFFERENCE"),

    ("PAY_0049", 4100, "AMOUNT_MISMATCH"),
    ("PAY_0050", 3900, "DATE_VARIANCE"),
    ("PAY_0051", 2700, "MISSING_BANK"),
    ("PAY_0052", 3300, "DUPLICATE"),
    ("PAY_0053", 4700, "REFUND_DIFFERENCE"),
    ("PAY_0054", 5600, "FEE_TAX_MISMATCH"),
    ("PAY_0055", 6200, "SOURCE_CONFLICT"),
    ("PAY_0056", 7100, "UNRESOLVED_DIFFERENCE"),
])


ledger_rows = []
bank_rows = []
razorpay_rows = []
adjustment_rows = []
ground_truth_rows = []


# ============================================================
# GENERATE RECORDS
# ============================================================

for index, (payment_id, amount, issue) in enumerate(transactions):

    tx_date = START + timedelta(
        days=index % 20
    )


    # --------------------------------------------------------
    # LEDGER
    # --------------------------------------------------------

    ledger_rows.append({
        "payment_id": payment_id,
        "transaction_date": tx_date.isoformat(),
        "amount": f"{amount:.2f}",
        "status": "SUCCESS"
    })


    # --------------------------------------------------------
    # BANK
    # --------------------------------------------------------

    if issue != "MISSING_BANK":

        bank_date = tx_date

        bank_amount = amount

        if issue == "AMOUNT_MISMATCH":

            bank_amount = amount - 300


        # SOURCE_CONFLICT:
        # Bank agrees with ledger.
        # Razorpay will disagree later.

        if issue == "SOURCE_CONFLICT":

            bank_amount = amount


        bank_rows.append({
            "payment_id": payment_id,
            "transaction_date": bank_date.isoformat(),
            "credit_amount": f"{bank_amount:.2f}"
        })


        # DUPLICATE:
        # Add a second bank record.

        if issue == "DUPLICATE":

            bank_rows.append({
                "payment_id": payment_id,
                "transaction_date": tx_date.isoformat(),
                "credit_amount": f"{amount:.2f}"
            })


    # --------------------------------------------------------
    # RAZORPAY SETTLEMENT
    # --------------------------------------------------------

    settlement_days = 2

    if issue == "DATE_VARIANCE":

        settlement_days = 5


    gross_amount = amount

    fee = amount * 0.02

    tax = amount * 0.0036

    net_amount = gross_amount - fee - tax


    # FEE/TAX MISMATCH:
    # Net amount intentionally does not equal
    # gross - fee - tax.

    if issue == "FEE_TAX_MISMATCH":

        net_amount = amount * 0.9700


    # SOURCE CONFLICT:
    # Ledger = Bank
    # Razorpay gross = Ledger + 250
    #
    # Razorpay net remains internally consistent.

    if issue == "SOURCE_CONFLICT":

        gross_amount = amount + 250

        net_amount = gross_amount - fee - tax


    # UNRESOLVED DIFFERENCE:
    # Ledger != Bank
    # Razorpay gross != Ledger
    # Razorpay calculation itself remains internally consistent.
    #
    # This should be detected as an unresolved multi-source
    # disagreement rather than a fee/tax mismatch.

    if issue == "UNRESOLVED_DIFFERENCE":

        bank_amount = amount - 200

        # Update the already-created bank record.

        bank_rows[-1]["credit_amount"] = f"{bank_amount:.2f}"

        gross_amount = amount + 400

        net_amount = gross_amount - fee - tax


    razorpay_rows.append({
        "payment_id": payment_id,
        "settlement_date": (
            tx_date + timedelta(days=settlement_days)
        ).isoformat(),
        "gross_amount": f"{gross_amount:.2f}",
        "fee": f"{fee:.2f}",
        "tax": f"{tax:.2f}",
        "net_amount": f"{net_amount:.2f}"
    })


    # --------------------------------------------------------
    # REFUND
    # --------------------------------------------------------

    if issue == "REFUND_DIFFERENCE":

        adjustment_rows.append({
            "payment_id": payment_id,
            "type": "REFUND",
            "amount": "200.00"
        })


    # --------------------------------------------------------
    # GROUND TRUTH
    # --------------------------------------------------------

    if issue != "MATCHED":

        ground_truth_rows.append({
            "payment_id": payment_id,
            "exception_type": issue
        })


# ============================================================
# WRITE CSV
# ============================================================

def write_csv(path, rows, fields):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()

        writer.writerows(rows)


write_csv(
    RAW / "ledger.csv",
    ledger_rows,
    [
        "payment_id",
        "transaction_date",
        "amount",
        "status"
    ]
)


write_csv(
    RAW / "bank.csv",
    bank_rows,
    [
        "payment_id",
        "transaction_date",
        "credit_amount"
    ]
)


write_csv(
    RAW / "razorpay.csv",
    razorpay_rows,
    [
        "payment_id",
        "settlement_date",
        "gross_amount",
        "fee",
        "tax",
        "net_amount"
    ]
)


write_csv(
    RAW / "adjustments.csv",
    adjustment_rows,
    [
        "payment_id",
        "type",
        "amount"
    ]
)


write_csv(
    GROUND_TRUTH,
    ground_truth_rows,
    [
        "payment_id",
        "exception_type"
    ]
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("DATASET CREATED")
print("================")

print(
    f"Transactions: {len(transactions)}"
)

print(
    f"Ledger records: {len(ledger_rows)}"
)

print(
    f"Bank records: {len(bank_rows)}"
)

print(
    f"Razorpay records: {len(razorpay_rows)}"
)

print(
    f"Adjustments: {len(adjustment_rows)}"
)

print(
    f"Ground-truth incidents: {len(ground_truth_rows)}"
)

print()
print("INCIDENT TYPES")
print("==============")

for issue in sorted(
    set(
        issue
        for _, _, issue in transactions
        if issue != "MATCHED"
    )
):

    count = sum(
        1
        for _, _, transaction_issue in transactions
        if transaction_issue == issue
    )

    print(
        f"{issue:<25} {count}"
    )