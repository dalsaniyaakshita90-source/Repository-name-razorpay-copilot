\# Razorpay Copilot



\### Evidence-Grounded Reconciliation \& Settlement Investigation Agent



Razorpay Copilot is an AI finance-operations prototype that reconciles payment records across multiple financial sources and investigates settlement discrepancies using evidence from the underlying records.



> \*\*Match what you can. Explain what you know. Flag what you don't.\*\*



\---



\## 🎯 Problem



Finance teams often need to reconcile:



\- Internal payment ledgers

\- Bank statements

\- Payment-gateway settlement records

\- Refunds and adjustments



Small discrepancies can require manual investigation across multiple sources.



Razorpay Copilot automates this reconciliation loop and turns detected exceptions into evidence-backed investigations.



\---



\## 🚀 What It Does



Razorpay Copilot:



1\. Processes a synthetic batch of payment records.

2\. Reconciles ledger, bank, and Razorpay settlement data.

3\. Detects financial exceptions.

4\. Classifies each exception.

5\. Calculates reconciliation performance.

6\. Provides evidence-backed answers to settlement questions.

7\. Refuses to guess when supporting evidence is unavailable.



\### Exception Types



\- Amount mismatch

\- Date variance

\- Missing bank record

\- Duplicate record

\- Refund difference

\- Fee/tax mismatch

\- Source conflict

\- Unresolved difference



\---



\## 🧠 AI Judgment \& Evidence Grounding



The Copilot does not blindly generate an answer.



For every investigation, it attempts to trace the answer back to the underlying financial records.



If sufficient evidence exists:



\*\*🟢 VERIFIED\*\*



If evidence is incomplete:



\*\*🟡 PARTIAL\*\*



If the available records cannot support a conclusion:



\*\*🔴 UNRESOLVED\*\*



This prevents the system from inventing explanations for financial discrepancies.



\---



\## 📊 Evaluation



The current synthetic evaluation contains \*\*5 known financial incidents\*\*.



| Metric | Result |

|---|---:|

| Ground-truth incidents | 5 |

| Detected exceptions | 5 |

| True positives | 5 |

| Missed incidents | 0 |

| False positives | 0 |

| Detection rate | \*\*100%\*\* |

| Classification rate | \*\*100%\*\* |



\### Classification Coverage



| Exception | Expected | Detected |

|---|---:|---:|

| AMOUNT\_MISMATCH | 1 | 1 |

| DATE\_VARIANCE | 1 | 1 |

| DUPLICATE | 1 | 1 |

| MISSING\_BANK | 1 | 1 |

| REFUND\_DIFFERENCE | 1 | 1 |



\---



\## 🏗️ Architecture



```text

&#x20;                ┌─────────────────────┐

&#x20;                │   Synthetic Data    │

&#x20;                └──────────┬──────────┘

&#x20;                           │

&#x20;            ┌──────────────┼──────────────┐

&#x20;            ▼              ▼              ▼

&#x20;       ┌─────────┐    ┌─────────┐    ┌────────────┐

&#x20;       │ Ledger  │    │  Bank   │    │ Razorpay   │

&#x20;       │ Records │    │ Records │    │ Settlement │

&#x20;       └────┬────┘    └────┬────┘    └─────┬──────┘

&#x20;            │              │               │

&#x20;            └──────────────┼───────────────┘

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │ Reconciliation      │

&#x20;                │ Engine              │

&#x20;                └──────────┬──────────┘

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │ Exception \&         │

&#x20;                │ Evidence Layer      │

&#x20;                └──────────┬──────────┘

&#x20;                           ▼

&#x20;                ┌─────────────────────┐

&#x20;                │ Settlement          │

&#x20;                │ Investigator        │

&#x20;                │ / Copilot           │

&#x20;                └─────────────────────┘

