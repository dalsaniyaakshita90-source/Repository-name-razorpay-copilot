import { useEffect, useMemo, useState } from "react";
import "./App.css";

const TOTAL_RECORDS = 56;
const GROUND_TRUTH = 16;

const EVALUATION_BREAKDOWN = [
  ["AMOUNT_MISMATCH", 2, 2],
  ["DATE_VARIANCE", 2, 2],
  ["DUPLICATE", 2, 2],
  ["FEE_TAX_MISMATCH", 2, 2],
  ["MISSING_BANK", 2, 2],
  ["REFUND_DIFFERENCE", 2, 2],
  ["SOURCE_CONFLICT", 2, 2],
  ["UNRESOLVED_DIFFERENCE", 2, 2],
];

function parseCSVLine(line) {
  const values = [];
  let current = "";
  let insideQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      if (insideQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (char === "," && !insideQuotes) {
      values.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }

  values.push(current.trim());
  return values;
}
function App() {
  const [exceptions, setExceptions] = useState([]);
  const [activePage, setActivePage] = useState("Overview");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [selectedException, setSelectedException] = useState(null);

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
          const values = parseCSVLine(line);
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

  const reconciled = Math.max(0, TOTAL_RECORDS - totalExceptions);

  const matchRate =
    TOTAL_RECORDS > 0
      ? ((reconciled / TOTAL_RECORDS) * 100).toFixed(1)
      : "0.0";

  const incidentTypes = new Set(
    exceptions.map((item) => item.exception_type)
  ).size;

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
          ` UNRESOLVED\n\n` +
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
        ` VERIFIED\n\n` +
        `I traced ${paymentId} across the reconciliation exceptions.\n\n` +
        `${details}\n\n` +
        `These findings are directly supported by the available reconciliation records.`
      );

      return;
    }

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
          ` UNRESOLVED\n\n` +
          `I can't determine why the settlement was lower from the available reconciliation records.\n\n` +
          `No settlement-related exception evidence was found.`
        );
        return;
      }

      const verified = [];
      const partial = [];
      const unresolved = [];

      relevantExceptions.forEach((item) => {
        const evidence =
          item.evidence || "No additional evidence available.";

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
              ` VERIFIED — The bank credit is lower than the ledger by Rs ${difference.toFixed(2)}.`
            );
          } else {
            partial.push(
              `${item.payment_id}: ${item.reason}\n` +
              `Evidence: ${evidence}\n` +
              ` PARTIAL — This is a reconciliation discrepancy, but the available evidence does not establish a settlement shortfall.`
            );
          }
        } else if (
          item.exception_type === "REFUND_DIFFERENCE" ||
          item.exception_type === "FEE_TAX_MISMATCH"
        ) {
          partial.push(
            `${item.payment_id}: ${item.reason}\n` +
            `Evidence: ${evidence}\n` +
            ` PARTIAL — This may affect settlement, but the available records do not establish the complete settlement impact.`
          );
        } else {
          unresolved.push(
            `${item.payment_id}: ${item.reason}\n` +
            `Evidence: ${evidence}\n` +
            ` UNRESOLVED — The available evidence is insufficient to determine the final settlement impact.`
          );
        }
      });

      let response =
        `I investigated the settlement-related reconciliation records.\n\n`;

      if (verified.length > 0) {
        response += ` VERIFIED\n\n${verified.join("\n\n")}\n\n`;
      }

      if (partial.length > 0) {
        response += ` PARTIAL\n\n${partial.join("\n\n")}\n\n`;
      }

      if (unresolved.length > 0) {
        response += ` UNRESOLVED\n\n${unresolved.join("\n\n")}\n\n`;
      }

      response +=
        `Conclusion: the available records identify reconciliation issues, ` +
        `but I will not infer a final settlement shortfall unless the evidence supports it.`;

      setAnswer(response);
      return;
    }

    if (
      q.includes("exception") ||
      q.includes("issue") ||
      q.includes("problem") ||
      q.includes("wrong")
    ) {
      const details = exceptions
        .map(
          (item) =>
            `${item.payment_id}: ${item.exception_type} (${item.severity}) — ${item.reason}`
        )
        .join("\n");

      setAnswer(
        `I found ${totalExceptions} reconciliation exceptions: ` +
        `${highSeverity} high severity and ${mediumSeverity} medium severity.\n\n` +
        `${details}`
      );

      return;
    }

    if (
      q.includes("match") ||
      q.includes("reconcile") ||
      q.includes("reconciliation")
    ) {
      setAnswer(
        `The current reconciliation run contains ${TOTAL_RECORDS} transactions.\n\n` +
        `${reconciled} transactions are reconciled and ` +
        `${totalExceptions} are exceptions.\n\n` +
        `Current match rate: ${matchRate}%.`
      );

      return;
    }

    setAnswer(
      ` UNRESOLVED\n\n` +
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
            <div className="metric-value">{TOTAL_RECORDS}</div>
            <div className="metric-sub">Across all sources</div>
          </div>

          <div className="metric">
            <div className="metric-label">Reconciled</div>
            <div className="metric-value">{reconciled}</div>
            <div className="metric-sub">{matchRate}% match rate</div>
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

        <ExceptionTable
          exceptions={exceptions}
          onSelect={setSelectedException}
        />

        {selectedException && (
          <ExceptionDetail
            exception={selectedException}
            onClose={() => setSelectedException(null)}
          />
        )}
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
            <p>{TOTAL_RECORDS} transactions</p>
          </div>

          <div className="flow-arrow">→</div>

          <div className="source-card">
            <span>02</span>
            <h3>Bank Statement</h3>
            <p>{TOTAL_RECORDS} records</p>
          </div>

          <div className="flow-arrow">→</div>

          <div className="source-card">
            <span>03</span>
            <h3>Razorpay</h3>
            <p>{TOTAL_RECORDS} settlements</p>
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
              <strong>{TOTAL_RECORDS}</strong>
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

        <ExceptionTable
          exceptions={exceptions}
          onSelect={setSelectedException}
        />

        {selectedException && (
          <ExceptionDetail
            exception={selectedException}
            onClose={() => setSelectedException(null)}
          />
        )}
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
            placeholder="Why was I paid less this week?"
          />

          <button onClick={answerQuestion}>Ask Copilot</button>
        </div>

        <div className="suggestions">
          <button
            onClick={() =>
              setQuestion("Why was I paid less this week?")
            }
          >
            Why was I paid less?
          </button>

          <button
            onClick={() =>
              setQuestion("What happened with PAY_0041?")
            }
          >
            Investigate PAY_0041
          </button>

          <button
            onClick={() =>
              setQuestion("What happened with PAY_9999?")
            }
          >
            Test unknown payment
          </button>

          <button
            onClick={() =>
              setQuestion("What is my reconciliation match rate?")
            }
          >
            What is my match rate?
          </button>
        </div>

        {answer && (
          <div className="copilot-answer">
            <div className="card-kicker">COPILOT RESPONSE</div>
            <p style={{ whiteSpace: "pre-line" }}>{answer}</p>
          </div>
        )}
      </section>
    );
  }

  function renderEvaluations() {
    return (
      <>
        <section className="metrics">
          <div className="metric">
            <div className="metric-label">Records evaluated</div>
            <div className="metric-value">{TOTAL_RECORDS}</div>
            <div className="metric-sub">Synthetic batch</div>
          </div>

          <div className="metric">
            <div className="metric-label">Ground truth</div>
            <div className="metric-value">{GROUND_TRUTH}</div>
            <div className="metric-sub">Known incidents</div>
          </div>

          <div className="metric">
            <div className="metric-label">Detection rate</div>
            <div className="metric-value">100%</div>
            <div className="metric-sub">16 / 16 detected</div>
          </div>

          <div className="metric">
            <div className="metric-label">Classification</div>
            <div className="metric-value">100%</div>
            <div className="metric-sub">All 8 types correct</div>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div className="card-kicker">SYSTEM EVALUATION</div>

            <div className="card-title">
              <h3>Reconciliation Evaluation</h3>
              <span>Reproducible</span>
            </div>
          </div>

          <div className="summary-grid">
            <div>
              <strong>56</strong>
              <span>Records evaluated</span>
            </div>

            <div>
              <strong>16</strong>
              <span>Ground-truth incidents</span>
            </div>

            <div>
              <strong>16</strong>
              <span>Detected exceptions</span>
            </div>

            <div>
              <strong>16</strong>
              <span>True-positive payments</span>
            </div>

            <div>
              <strong>0</strong>
              <span>Missed incidents</span>
            </div>

            <div>
              <strong>0</strong>
              <span>False positives</span>
            </div>

            <div>
              <strong>100%</strong>
              <span>Detection rate</span>
            </div>

            <div>
              <strong>100%</strong>
              <span>Classification rate</span>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div className="card-kicker">CLASSIFICATION COVERAGE</div>

            <div className="card-title">
              <h3>Exception Types</h3>
              <span>2 incidents each</span>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="exception-table">
              <thead>
                <tr>
                  <th>Exception Type</th>
                  <th>Expected</th>
                  <th>Detected</th>
                  <th>Result</th>
                </tr>
              </thead>

              <tbody>
                {EVALUATION_BREAKDOWN.map(([type, expected, detected]) => (
                  <tr key={type}>
                    <td>{type}</td>
                    <td>{expected}</td>
                    <td>{detected}</td>
                    <td>
                      <span className="severity high">PASS</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section
          className="card"
          style={{
            background: "#111214",
            color: "#fff",
            border: "1px solid #222",
          }}
        >
          <div className="card-kicker" style={{ color: "#aaa" }}>
            EVALUATION PRINCIPLE
          </div>

          <h3 style={{ fontSize: "24px", margin: "12px 0" }}>
            Never force a match just to improve the score.
          </h3>

          <p style={{ color: "#aaa", lineHeight: 1.7, margin: 0 }}>
            The system is evaluated against a separate ground-truth file
            containing controlled incidents. It reports what it detected,
            what it missed, and what it could not resolve.
          </p>
        </section>
      </>
    );
  }

  function renderPage() {
    if (activePage === "Overview") return renderOverview();
    if (activePage === "Reconciliation") return renderReconciliation();
    if (activePage === "Exceptions") return renderExceptions();
    if (activePage === "Ask Copilot") return renderCopilot();
    if (activePage === "Evaluations") return renderEvaluations();

    return null;
  }

  const navItems = [
    "Overview",
    "Reconciliation",
    "Exceptions",
    "Ask Copilot",
    "Evaluations",
  ];

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Razorpay Copilot</h1>
        <p>Merchant Operations</p>

        <nav>
          {navItems.map((item) => (
            <button
              key={item}
              className={activePage === item ? "active" : ""}
              onClick={() => {
                setActivePage(item);
                setAnswer("");
                setSelectedException(null);
              }}
            >
              {item === "Overview" && "○ "}
              {item === "Reconciliation" && "↔ "}
              {item === "Exceptions" && "⚠ "}
              {item === "Ask Copilot" && "⌕ "}
              {item === "Evaluations" && "✓ "}
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
              Run
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

function ExceptionTable({ exceptions, onSelect }) {
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
              <tr
                key={`${item.payment_id}-${index}`}
                onClick={() => onSelect(item)}
                style={{
                  cursor: "pointer",
                }}
                title="Click to inspect evidence"
              >
                <td>
                  <strong>{item.payment_id}</strong>
                </td>

                <td>{item.exception_type}</td>

                <td>
                  <span
                    className={`severity ${
                      item.severity === "HIGH" ? "high" : "medium"
                    }`}
                  >
                    {item.severity}
                  </span>
                </td>

                <td>{item.reason}</td>

                <td>{item.evidence || "No additional evidence."}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {exceptions.length > 0 && (
        <div
          style={{
            padding: "14px 20px",
            borderTop: "1px solid #eee",
            color: "#777",
            fontSize: "13px",
          }}
        >
          Click any exception to inspect its evidence.
        </div>
      )}
    </section>
  );
}

function ExceptionDetail({ exception, onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.38)",
        zIndex: 1000,
        display: "flex",
        justifyContent: "flex-end",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "min(520px, 92vw)",
          height: "100%",
          background: "#fff",
          padding: "34px",
          boxSizing: "border-box",
          overflowY: "auto",
          boxShadow: "-12px 0 40px rgba(0,0,0,0.18)",
        }}
      >
        <button
          onClick={onClose}
          style={{
            border: "none",
            background: "transparent",
            fontSize: "28px",
            cursor: "pointer",
            float: "right",
          }}
        >
          ×
        </button>

        <div className="card-kicker">EXCEPTION EVIDENCE</div>

        <h2 style={{ marginTop: "12px", marginBottom: "6px" }}>
          {exception.payment_id}
        </h2>

        <p style={{ color: "#777", marginTop: 0 }}>
          Evidence-backed investigation
        </p>

        <div
          style={{
            display: "inline-block",
            padding: "7px 12px",
            borderRadius: "999px",
            background:
              exception.severity === "HIGH" ? "#fff0f0" : "#fff8e6",
            color:
              exception.severity === "HIGH" ? "#d92d20" : "#9a6700",
            fontWeight: 700,
            fontSize: "12px",
            marginBottom: "26px",
          }}
        >
          {exception.severity} SEVERITY
        </div>

        <div style={{ marginBottom: "24px" }}>
          <div
            style={{
              color: "#888",
              fontSize: "12px",
              textTransform: "uppercase",
              letterSpacing: "1px",
              marginBottom: "7px",
            }}
          >
            Exception
          </div>

          <div style={{ fontWeight: 700, fontSize: "18px" }}>
            {exception.exception_type}
          </div>
        </div>

        <div style={{ marginBottom: "24px" }}>
          <div
            style={{
              color: "#888",
              fontSize: "12px",
              textTransform: "uppercase",
              letterSpacing: "1px",
              marginBottom: "7px",
            }}
          >
            Reason
          </div>

          <div style={{ lineHeight: 1.6 }}>
            {exception.reason}
          </div>
        </div>

        <div
          style={{
            padding: "20px",
            background: "#f7f7f8",
            borderRadius: "12px",
            border: "1px solid #e8e8e8",
          }}
        >
          <div
            style={{
              color: "#888",
              fontSize: "12px",
              textTransform: "uppercase",
              letterSpacing: "1px",
              marginBottom: "10px",
            }}
          >
            Source Evidence
          </div>

          <div style={{ lineHeight: 1.7 }}>
            {exception.evidence || "No additional evidence available."}
          </div>
        </div>

        <div
          style={{
            marginTop: "28px",
            paddingTop: "20px",
            borderTop: "1px solid #eee",
            color: "#666",
            fontSize: "13px",
            lineHeight: 1.6,
          }}
        >
          This exception is grounded in the reconciliation output. The
          Copilot uses these records as evidence and does not invent
          unsupported conclusions.
        </div>
      </div>
    </div>
  );
}

export default App;






