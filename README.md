# Razorpay Copilot

### Evidence-Grounded Reconciliation & Settlement Investigation Agent

Razorpay Copilot is an AI finance-operations prototype that reconciles payment records across multiple financial sources and investigates settlement discrepancies using evidence from the underlying records.

> **Match what you can. Explain what you know. Flag what you don't.**

---

## 🎯 Problem

Finance teams often need to reconcile:

- Internal payment ledgers
- Bank statements
- Payment-gateway settlement records
- Refunds and adjustments

Small discrepancies can require manual investigation across multiple sources.

Razorpay Copilot automates this reconciliation loop and turns detected exceptions into evidence-backed investigations.

---

## 🚀 What It Does

Razorpay Copilot:

1. Processes a synthetic batch of payment records.
2. Reconciles ledger, bank, and Razorpay settlement data.
3. Detects financial exceptions.
4. Classifies each exception.
5. Calculates reconciliation performance.
6. Provides evidence-backed answers to settlement questions.
7. Refuses to guess when supporting evidence is unavailable.

### Exception Types

- Amount mismatch
- Date variance
- Missing bank record
- Duplicate record
- Refund difference
- Fee/tax mismatch
- Source conflict
- Unresolved difference

---

## 🧠 AI Judgment & Evidence Grounding

The Copilot does not blindly generate an answer.

For every investigation, it attempts to trace the answer back to the underlying financial records.

If sufficient evidence exists:

**🟢 VERIFIED**

If evidence is incomplete:

**🟡 PARTIAL**

If the available records cannot support a conclusion:

**🔴 UNRESOLVED**

This prevents the system from inventing explanations for financial discrepancies.

---

## 📊 Evaluation

The current synthetic evaluation contains **5 known financial incidents affecting 5 payments**.

| Metric | Result |
|---|---:|
| Ground-truth incidents | 5 |
| Detected exception rows | 6 |
| True-positive payments | 5 |
| Missed incidents | 0 |
| False-positive payments | 0 |
| Detection rate | **100%** |
| Classification rate | **100%** |

> **Note:** 5 injected incidents affected 5 payments. One affected payment (`PAY_0009`) produced two exception signals, so the engine surfaced **6 exception rows** while detecting all **5 injected incidents**.

### Classification Coverage

| Exception | Expected | Detected |
|---|---:|---:|
| AMOUNT_MISMATCH | 1 | 1 |
| DATE_VARIANCE | 1 | 1 |
| DUPLICATE | 1 | 1 |
| MISSING_BANK | 1 | 1 |
| REFUND_DIFFERENCE | 1 | 1 |

## 🏗️ Architecture

```text
                 │ / Copilot           │
                 └─────────────────────┘
                 ┌─────────────────────┐
                 │   Synthetic Data    │
                 └──────────┬──────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        ┌─────────┐    ┌─────────┐    ┌────────────┐
        │ Ledger  │    │  Bank   │    │ Razorpay   │
        │ Records │    │ Records │    │ Settlement │
        └────┬────┘    └────┬────┘    └─────┬──────┘
             │              │               │
             └──────────────┼───────────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Reconciliation      │
                 │ Engine              │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Exception &         │
                 │ Evidence Layer      │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Settlement          │
                 │ Investigator        │
                 │ / Copilot           │
                 └─────────────────────┘

💬 Example Investigations

Verified Exception

Question:

What happened with PAY_0009?

The Copilot traces the payment to its underlying records and identifies the relevant exceptions, including the duplicate bank record and amount discrepancy.

Unresolved Case

Question:

What happened with PAY_9999?

The Copilot does not invent an explanation because no supporting record exists.

Settlement Investigation

Question:

Why was I paid less this week?

The Copilot identifies relevant settlement exceptions and explains which records provide evidence for the discrepancy.

🛠️ Tech Stack
Python
React
Vite
JavaScript
CSV-based synthetic financial data
Git / GitHub

📁 Project Structure
razorpay-copilot/
│
├── backend/
│   ├── generate_data.py
│   └── reconcile.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── ground_truth/
│
├── evaluation/
│   └── evaluate_reconciliation.py
│
├── frontend/
│   ├── public/
│   └── src/
│
├── .gitignore
└── README.md

▶️ Running the Project
Backend
cd backend
python generate_data.py
python reconcile.py

Evaluation 
cd evaluation
python evaluate_reconciliation.py

Frontend 
cd frontend
npm run dev

Open the local Vite URL shown in the terminal.

🎯 Buildathon Track

Built for:

Razorpay AI Buildathon — Track 04: AI Finance Controller

The prototype focuses on closing a finance-operations loop through:

Multi-source reconciliation
Measured exception detection
Exception classification
Settlement investigation
Evidence-grounded answers
Honest abstention when evidence is insufficient

🔑 Product Principle

It doesn't just answer. It proves.

And when it cannot prove — it says so.