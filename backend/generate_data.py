import csv
from datetime import date, timedelta

START = date(2026, 8, 1)

transactions = [
    ("PAY_0001", 2500, "MATCHED"),
    ("PAY_0002", 4200, "MATCHED"),
    ("PAY_0003", 1800, "MATCHED"),
    ("PAY_0004", 7500, "MATCHED"),
    ("PAY_0005", 3200, "MATCHED"),
    ("PAY_0006", 5000, "AMOUNT_MISMATCH"),
    ("PAY_0007", 6400, "DATE_VARIANCE"),
    ("PAY_0008", 2800, "MISSING_BANK"),
    ("PAY_0009", 3600, "DUPLICATE"),
    ("PAY_0010", 4500, "REFUND_DIFFERENCE"),
]

for i in range(11, 51):
    amount = 1500 + ((i * 731) % 6500)
    transactions.append(
        (f"PAY_{i:04d}", amount, "MATCHED")
    )

ledger_rows = []
bank_rows = []
razorpay_rows = []
adjustment_rows = []

for index, (payment_id, amount, issue) in enumerate(transactions):

    tx_date = START + timedelta(days=index % 20)

    ledger_rows.append({
        "payment_id": payment_id,
        "transaction_date": tx_date.isoformat(),
        "amount": f"{amount:.2f}",
        "status": "SUCCESS"
    })

    # BANK
    if issue != "MISSING_BANK":

        bank_date = tx_date

        if issue == "DATE_VARIANCE":
            bank_date = tx_date + timedelta(days=1)

        bank_amount = amount

        if issue == "AMOUNT_MISMATCH":
            bank_amount = amount - 300

        bank_rows.append({
            "payment_id": payment_id,
            "transaction_date": bank_date.isoformat(),
            "credit_amount": f"{bank_amount:.2f}"
        })

        # Duplicate bank record
        if issue == "DUPLICATE":
            bank_rows.append({
                "payment_id": payment_id,
                "transaction_date": tx_date.isoformat(),
                "credit_amount": f"{amount:.2f}"
            })

    # RAZORPAY
    razorpay_rows.append({
        "payment_id": payment_id,
        "settlement_date": (
            tx_date + timedelta(days=(4 if issue == "DATE_VARIANCE" else 2))
        ).isoformat(),
        "gross_amount": f"{amount:.2f}",
        "fee": f"{amount * 0.02:.2f}",
        "tax": f"{amount * 0.0036:.2f}",
        "net_amount": f"{amount * 0.9764:.2f}"
    })

    # REFUND
    if issue == "REFUND_DIFFERENCE":
        adjustment_rows.append({
            "payment_id": payment_id,
            "type": "REFUND",
            "amount": "200.00"
        })


def write_csv(path, rows, fields):

    with open(path, "w", newline="") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)


write_csv(
    "data/raw/ledger.csv",
    ledger_rows,
    [
        "payment_id",
        "transaction_date",
        "amount",
        "status"
    ]
)

write_csv(
    "data/raw/bank.csv",
    bank_rows,
    [
        "payment_id",
        "transaction_date",
        "credit_amount"
    ]
)

write_csv(
    "data/raw/razorpay.csv",
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
    "data/raw/adjustments.csv",
    adjustment_rows,
    [
        "payment_id",
        "type",
        "amount"
    ]
)

print("DATASET CREATED")
print("================")
print(f"Ledger records: {len(ledger_rows)}")
print(f"Bank records: {len(bank_rows)}")
print(f"Razorpay records: {len(razorpay_rows)}")
print(f"Adjustments: {len(adjustment_rows)}")
print()
print("Known demo incidents:")
print("AMOUNT_MISMATCH")
print("DATE_VARIANCE")
print("MISSING_BANK")
print("DUPLICATE")
print("REFUND_DIFFERENCE")
