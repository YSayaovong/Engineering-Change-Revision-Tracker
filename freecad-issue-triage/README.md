# FreeCAD issue triage

This dashboard explores what remained open and how issues were closed for the 64 issues opened in FreeCAD from January 25–31, 2026 (UTC). The snapshot was retrieved November 18, 2026. The issue-type filter updates the counts, charts, and linked open-issue list.

Of 44 closed issues, 31 were marked completed, 9 duplicate, and 4 not planned. Median time to close was 6.6 calendar days across the 44 closures. The 20 open issues are outside that median.

- [FreeCAD issue tracker](https://github.com/FreeCAD/FreeCAD/issues)
- `data.json` contains the reviewed issue records and query method.
- `DashboardContent.jsx` and `dashboard.css` are the authored dashboard layer for the ChatGPT Work Data dashboard runtime.

To rebuild with that runtime, initialize a dashboard with `data.json` as its snapshot, copy the JSX and CSS into `src/content/dashboard/`, and use the runtime's build and portable HTML export commands.
