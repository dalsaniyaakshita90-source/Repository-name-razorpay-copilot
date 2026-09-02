import { useEffect, useMemo, useState } from "react";
import "./App.css";

function App() {
  const [exceptions, setExceptions] = useState([]);
  const [activePage, setActivePage] = useState("Overview");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  useEffect(() => {
    fetch("/exceptions.csv")
      .then((response) => response.text())
      .then((text) => {
        const lines = text.trim().split("\n");

        if (lines.length <= 1) {
          setExceptions([]);
          return;
        }

        const headers = lines[0].split(",");

        const rows = lines.slice(1).map((line) => {
          const values = line.split(",");
          const row = {};

          headers.forEach((header, index) => {
            row[header.trim()] = (values[index] || "").trim();
          });

          return row;
        });

        setExceptions(rows);
      })
      .catch((error) => {
        console.error("Could not load exceptions:", error);
      });
  }, []);

  const totalExceptions = exceptions.length;

  const highSeverity = exceptions.filter(
    (item) => item.severity === "HIGH"
  ).length;

  const mediumSeverity = exceptions.filter(
    (item) => item.severity === "MEDIUM"
  ).length;

  const incidentTypes = new Set(
    exceptions.map((item) => item.exception_type)
  ).size;

  const reconciled = Math.max(0, 50 - totalExceptions);

  const matchRate =
    50 > 0 ? ((reconciled / 50) * 100).toFixed(1) : "0.0";

  const exceptionSummary = useMemo(() => {
    const counts = {};

    exceptions.forEach((item) => {
      counts[item.exception_type] =
        (counts[item.exception_type] || 0) + 1;
    });

    return counts;
  }, [exceptions]);

 function answerQuestion() {
  const q = question.toLowerCase().trim();

  if (!q) {
    setAnswer("Please enter a question about the reconciliation data.");
    return;
  }

  // ---------------------------------------------------------
  // 1. PAYMENT-SPECIFIC INVESTIGATION
  // ---------------------------------------------------------

  const paymentMatch = q.match(/pay[_\s-]?\d+/i);

  if (paymentMatch) {
    const paymentId = paymentMatch[0]
      .replace(/\s|-/g, "_")
      .toUpperCase();

    const matches = exceptions.filter(
      (item) =>
        item.payment_id &&
        item.payment_id.toUpperCase() === paymentId
    );

    if (matches.length === 0) {
      setAnswer(
        `🔴 UNRESOLVED\n\n` +
        `I can't determine what happened with ${paymentId} from the available reconciliation records.\n\n` +
        `No matching exception evidence was found for this payment. ` +
        `I won't infer a result without supporting records.`
      );
      return;
    }

    const details = matches
      .map((item) => {
        const evidence = item.evidence
          ? `Evidence: ${item.evidence}`
          : "Evidence: No additional evidence available.";

        return (
          `${item.exception_type} — ${item.severity}\n` +
          `${item.reason}\n` +
          `${evidence}`
        );
      })
      .join("\n\n");

    setAnswer(
      `🟢 VERIFIED\n\n` +
      `I traced ${paymentId} across the reconciliation exceptions.\n\n` +
      `${details}\n\n` +
      `These findings are directly supported by the available reconciliation records.`
    );

    return;
  }

  // ---------------------------------------------------------
  // 2. "WHY WAS I PAID LESS?" / SETTLEMENT INVESTIGATION
  // ---------------------------------------------------------

  if (
    q.includes("paid less") ||
    q.includes("short") ||
    q.includes("settlement") ||
    q.includes("settled less") ||
    q.includes("loss") ||
    q.includes("lost")
  ) {
    const relevantExceptions = exceptions.filter((item) =>
      [
        "AMOUNT_MISMATCH",
        "REFUND_DIFFERENCE",
        "FEE_TAX_MISMATCH",
        "SOURCE_CONFLICT",
        "UNRESOLVED_DIFFERENCE",
      ].includes(item.exception_type)
    );

    if (relevantExceptions.length === 0) {
      setAnswer(
        `🔴 UNRESOLVED\n\n` +
        `I can't determine why the settlement was lower from the available reconciliation records.\n\n` +
        `No settlement-related exception evidence was found.`
      );
      return;
    }

    const verified = [];
    const partial = [];
    const unresolved = [];

    relevantExceptions.forEach((item) => {
      const evidence = item.evidence || "No additional evidence available.";

      if (item.exception_type === "AMOUNT_MISMATCH") {
        const differenceMatch = evidence.match(
          /Difference:\s*Rs\s*(-?[\d.]+)/i
        );

        const difference = differenceMatch
          ? parseFloat(differenceMatch[1])
          : null;

        if (difference !== null && difference > 0) {
          verified.push(
            `${item.payment_id}: ${item.reason}\n` +
            `Evidence: ${evidence}\n` +
            `🟢 VERIFIED — The bank credit is lower than the ledger by Rs ${difference.toFixed(2)}.`
          );
        } else {
          partial.push(
            `${item.payment_id}: ${item.reason}\n` +
            `Evidence: ${evidence}\n` +
            `🟡 PARTIAL — This is a reconciliation discrepancy, but the available evidence does not establish a settlement shortfall.`
          );
        }
      } else if (
        item.exception_type === "REFUND_DIFFERENCE" ||
        item.exception_type === "FEE_TAX_MISMATCH"
      ) {
        partial.push(
          `${item.payment_id}: ${item.reason}\n` +
          `Evidence: ${evidence}\n` +
          `🟡 PARTIAL — This may affect settlement, but the available records do not establish the complete settlement impact.`
        );
      } else {
        unresolved.push(
          `${item.payment_id}: ${item.reason}\n` +
          `Evidence: ${evidence}\n` +
          `🔴 UNRESOLVED — The available evidence is insufficient to determine the final settlement impact.`
        );
      }
    });

    let response =
      `I investigated the settlement-related reconciliation records.\n\n`;

    if (verified.length > 0) {
      response +=
        `🟢 VERIFIED\n\n${verified.join("\n\n")}\n\n`;
    }

    if (partial.length > 0) {
      response +=
        `🟡 PARTIAL\n\n${partial.join("\n\n")}\n\n`;
    }

    if (unresolved.length > 0) {
      response +=
        `🔴 UNRESOLVED\n\n${unresolved.join("\n\n")}\n\n`;
    }

    response +=
      `Conclusion: the available records identify reconciliation issues, ` +
      `but I will not infer a final settlement shortfall unless the evidence supports it.`;

    setAnswer(response);

    return;
  }

  // ---------------------------------------------------------
  // 3. EXCEPTION SUMMARY
  // ---------------------------------------------------------

  if (
    q.includes("exception") ||
    q.includes("issue") ||
    q.includes("problem")
  ) {
    const highSeverity = exceptions.filter(
      (item) => item.severity === "HIGH"
    ).length;

    const mediumSeverity = exceptions.filter(
      (item) => item.severity === "MEDIUM"
    ).length;

    const details = exceptions
      .map(
        (item) =>
          `${item.payment_id}: ${item.exception_type} (${item.severity}) — ${item.reason}`
      )
      .join("\n");

    setAnswer(
      `I found ${exceptions.length} reconciliation exceptions: ` +
      `${highSeverity} high severity and ${mediumSeverity} medium severity.\n\n` +
      `${details}`
    );

    return;
  }

  // ---------------------------------------------------------
  // 4. RECONCILIATION / MATCH RATE
  // ---------------------------------------------------------

  if (
    q.includes("match") ||
    q.includes("reconcile") ||
    q.includes("reconciliation")
  ) {
    setAnswer(
      `The current reconciliation run contains 50 transactions.\n\n` +
      `${reconciled} transactions are reconciled and ` +
      `${totalExceptions} are exceptions.\n\n` +
      `Current match rate: ${matchRate}%.`
    );

    return;
  }

  // ---------------------------------------------------------
  // 5. DEFAULT / ABSTENTION
  // ---------------------------------------------------------

  setAnswer(
    `🔴 UNRESOLVED\n\n` +
    `I can't answer that from the current reconciliation dataset.\n\n` +
    `I can investigate payment IDs, settlement differences, ` +
    `reconciliation exceptions, and match rates using the available records.`
  );
}

  function renderOverview() {
    return (
      <>
        <section className="metrics">
          <div className="metric">
            <div className="metric-label">Transactions</div>
            <div className="metric-value">50</div>
            <div className="metric-sub">Across all sources</div>
          </div>

          <div className="metric">
            <div className="metric-label">Reconciled</div>
            <div className="metric-value">{reconciled}</div>
            <div className="metric-sub">
              {matchRate}% match rate
            </div>
          </div>

          <div className="metric">
            <div className="metric-label">Exceptions</div>
            <div className="metric-value">{totalExceptions}</div>
            <div className="metric-sub">Require attention</div>
          </div>

          <div className="metric">
            <div className="metric-label">High severity</div>
            <div className="metric-value">{highSeverity}</div>
            <div className="metric-sub">Priority issues</div>
          </div>
        </section>

        <ExceptionTable exceptions={exceptions} />
      </>
    );
  }

  function renderReconciliation() {
    return (
      <>
        <section className="reconciliation-flow">
          <div className="source-card">
            <span>01</span>
            <h3>Internal Ledger</h3>
            <p>50 transactions</p>
          </div>

          <div className="flow-arrow">→</div>

          <div className="source-card">
            <span>02</span>
            <h3>Bank Statement</h3>
            <p>50 records</p>
          </div>

          <div className="flow-arrow">→</div>

          <div className="source-card">
            <span>03</span>
            <h3>Razorpay</h3>
            <p>50 settlements</p>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div className="card-kicker">RECONCILIATION RESULT</div>
            <div className="card-title">
              <h3>Run Summary</h3>
              <span>{matchRate}% matched</span>
            </div>
          </div>

          <div className="summary-grid">
            <div>
              <strong>50</strong>
              <span>Transactions processed</span>
            </div>

            <div>
              <strong>{reconciled}</strong>
              <span>Successfully reconciled</span>
            </div>

            <div>
              <strong>{totalExceptions}</strong>
              <span>Exceptions generated</span>
            </div>

            <div>
              <strong>{incidentTypes}</strong>
              <span>Incident types</span>
            </div>
          </div>
        </section>
      </>
    );
  }

  function renderExceptions() {
    return (
      <>
        <section className="exception-summary">
          {Object.entries(exceptionSummary).map(([type, count]) => (
            <div className="summary-item" key={type}>
              <span>{type}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </section>

        <ExceptionTable exceptions={exceptions} />
      </>
    );
  }

  function renderCopilot() {
    return (
      <section className="copilot-card">
        <div className="card-kicker">COPILOT INTELLIGENCE</div>

        <h3>Ask about your reconciliation</h3>

        <p>
          Ask questions about exceptions, match rate, severity, or
          reconciliation status. The Copilot only answers from the
          available evidence.
        </p>

        <div className="question-box">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                answerQuestion();
              }
            }}
            placeholder="Why do I have reconciliation exceptions?"
          />

          <button onClick={answerQuestion}>
            Ask Copilot
          </button>
        </div>

        <div className="suggestions">
          <button
            onClick={() =>
              setQuestion("Why do I have reconciliation exceptions?")
            }
          >
            Why do I have exceptions?
          </button>

          <button
            onClick={() =>
              setQuestion("What is my reconciliation match rate?")
            }
          >
            What is my match rate?
          </button>

          <button
            onClick={() =>
              setQuestion("Which issues are high severity?")
            }
          >
            Which issues are high severity?
          </button>
        </div>

        {answer && (
          <div className="copilot-answer">
            <div className="card-kicker">COPILOT RESPONSE</div>
            <p>{answer}</p>
          </div>
        )}
      </section>
    );
  }

  function renderPage() {
    if (activePage === "Overview") {
      return renderOverview();
    }

    if (activePage === "Reconciliation") {
      return renderReconciliation();
    }

    if (activePage === "Exceptions") {
      return renderExceptions();
    }

    if (activePage === "Ask Copilot") {
      return renderCopilot();
    }

    return null;
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Razorpay Copilot</h1>
        <p>Merchant Operations</p>

        <nav>
          {[
            "Overview",
            "Reconciliation",
            "Exceptions",
            "Ask Copilot",
          ].map((item) => (
            <button
              key={item}
              className={activePage === item ? "active" : ""}
              onClick={() => {
                setActivePage(item);
                setAnswer("");
              }}
            >
              {item === "Overview" && "◇ "}
              {item === "Reconciliation" && "□ "}
              {item === "Exceptions" && "△ "}
              {item === "Ask Copilot" && "⌕ "}
              {item}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main">
        <div className="content">
          <header className="header">
            <div>
              <h2>
                {activePage === "Overview"
                  ? "Reconciliation Overview"
                  : activePage}
              </h2>

              <p>
                Trace every payment across your financial sources.
              </p>
            </div>

            <button
              className="run-button"
              onClick={() => window.location.reload()}
            >
              ↻ Run
              <br />
              reconciliation
            </button>
          </header>

          {renderPage()}
        </div>
      </main>
    </div>
  );
}

function ExceptionTable({ exceptions }) {
  return (
    <section className="card">
      <div className="card-header">
        <div className="card-kicker">EXCEPTION QUEUE</div>

        <div className="card-title">
          <h3>Detected Issues</h3>
          <span>{exceptions.length} exceptions</span>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="exception-table">
          <thead>
            <tr>
              <th>Payment ID</th>
              <th>Exception</th>
              <th>Severity</th>
              <th>Reason</th>
              <th>Evidence</th>
            </tr>
          </thead>

          <tbody>
            {exceptions.map((item, index) => (
              <tr key={`${item.payment_id}-${index}`}>
                <td>{item.payment_id}</td>

                <td>{item.exception_type}</td>

                <td>
                  <span
                    className={`severity ${
                      item.severity === "HIGH"
                        ? "high"
                        : "medium"
                    }`}
                  >
                    {item.severity}
                  </span>
                </td>

                <td>{item.reason}</td>

                <td>
                  {item.evidence || "No additional evidence."}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default App;
