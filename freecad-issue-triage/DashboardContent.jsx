import React, { useState } from "react";
import { DataComponent, EvidenceChart, MetricCard, useDataApp } from "../../data-app-public.jsx";
import "./dashboard.css";

const stages = [
  ["Under 1 day", 0, 1], ["1–6 days", 1, 7], ["7–29 days", 7, 30],
  ["30–89 days", 30, 90], ["90+ days", 90, Infinity],
];
const outcomes = [
  ["Completed", "completed"], ["Duplicate", "duplicate"],
  ["Not planned", "not_planned"], ["Unspecified", null],
];

function median(values) {
  const sorted = values.toSorted((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

export function DashboardContent() {
  const { reviewedRows } = useDataApp();
  const [selectedType, setSelectedType] = useState("");
  const all = reviewedRows("issues");
  const types = [...new Set(all.map(row => row.type))].sort();
  const rows = all.filter(row => !selectedType || row.type === selectedType);
  const closed = rows.filter(row => row.state === "closed");
  const open = rows.filter(row => row.state === "open");
  const byType = types.map(type => ({
    type,
    open: open.filter(row => row.type === type).length,
    closed: closed.filter(row => row.type === type).length,
  })).filter(row => row.open + row.closed).sort((a, b) => b.open + b.closed - a.open - a.closed);
  const byReason = outcomes.map(([reason, key]) => ({
    reason, issues: closed.filter(row => row.reason === key).length,
  }));
  const byTime = stages.map(([band, start, end]) => ({
    band, issues: closed.filter(row => row.days >= start && row.days < end).length,
  }));

  return <div className="issue-dashboard">
    <div className="issue-scope">
      <div><strong>Issues opened Jan 25–31, 2026 (UTC)</strong><br />
      <span>Snapshot taken Nov 18, 2026 · <a href="https://github.com/FreeCAD/FreeCAD/issues">FreeCAD issue tracker</a></span></div>
      <label>Issue type <select value={selectedType} onChange={event => setSelectedType(event.target.value)}>
        <option value="">All types</option>
        {types.map(type => <option key={type}>{type}</option>)}
      </select></label>
    </div>
    <div className="issue-metrics">
      <MetricCard id="total" title="Issues opened" value={rows.length} queryId="issues" sourceRows={rows} />
      <MetricCard id="open" title="Still open" value={open.length} queryId="issues" sourceRows={open} />
      <MetricCard id="closed" title="Closed" value={closed.length} queryId="issues" sourceRows={closed} />
      <MetricCard id="median" title="Median time to close" value={closed.length ? median(closed.map(row => row.days)).toFixed(1) + " days" : "—"} description="Calendar days for closed issues only" queryId="issues" sourceRows={closed} />
    </div>
    <EvidenceChart variant="card" id="issue-type-breakdown" title="Open and closed issues by type" queryId="issues"
      rows={byType} sourceRows={rows} height={300}
      spec={{type:"horizontalStackedBar", x:"type", y:"open", fields:["open","closed"], fieldLabels:{open:"Open",closed:"Closed"}}} />
    <div className="issue-charts">
      {closed.length ? <>
        <EvidenceChart variant="card" id="closure-reasons" title="Why issues were closed" queryId="issues"
          rows={byReason} sourceRows={closed} height={230}
          spec={{type:"horizontalBar",x:"reason",y:"issues"}} />
        <EvidenceChart variant="card" id="closure-times" title="How long issues took to close" queryId="issues"
          rows={byTime} sourceRows={closed} height={230}
          spec={{type:"bar",x:"band",y:"issues"}} />
      </> : <p>No closed issues in this selection.</p>}
    </div>
    <DataComponent variant="card" id="open-issue-list" title="Open issues to review" queryId="issues" sourceRows={open}>
      {open.length ? <div className="issue-scroll"><table>
        <thead><tr><th scope="col">Issue</th><th scope="col">Type</th><th scope="col">Opened (UTC)</th></tr></thead>
        <tbody>{open.toSorted((a,b) => a.opened.localeCompare(b.opened)).map(row =>
          <tr key={row.number}><td><a href={"https://github.com/FreeCAD/FreeCAD/issues/" + row.number}>#{row.number} {row.title}</a></td><td>{row.type}</td><td>{row.opened.slice(0,10)}</td></tr>
        )}</tbody>
      </table></div> : <p>No open issues in this selection.</p>}
    </DataComponent>
    <p className="issue-method">Issue type uses the first GitHub Type label, with missing labels shown as Unclassified. Closure time is elapsed calendar time, including duplicates and issues marked not planned. This one-week intake cohort represents a subset of the FreeCAD backlog.</p>
  </div>;
}

