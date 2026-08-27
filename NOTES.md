# Implementation notes

- The project uses server-rendered Django templates and ordinary session authentication.
- ReportLab is used for PDF export because it is installable without Pango/Cairo system packages. The PDF output is intentionally print-ready and can be branded further through the configured studio settings.
- Currency defaults to NPR (`रु`) because the supplied PRD targets a Nepal-focused deployment; this is configurable through `CURRENCY_SYMBOL`.
- `Enrollment.is_active` is the database-enforced allocation slot. Date-derived status remains computed from entry and exit dates, while expired/upcoming demo records use `is_active=False` so a student can be renewed without violating the current-slot constraint.
- The application currently has no attendance, automated reminders, online payment gateway, student/teacher portal, or multi-branch model by design.
