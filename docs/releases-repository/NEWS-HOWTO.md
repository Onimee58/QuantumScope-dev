# Editing QuantumScope's news (for the maintainers)

`news.json` in the public repository **Onimee58/QuantumScope** (on `main`) is what every copy of
QuantumScope 0.9.5 or later reads, at most once a week, if its user allowed it. Edit it on GitHub
(pencil icon → Commit changes). No new release is needed. Copies pick it up within a week.

```json
{
  "support_email": "help@quantumscope.example",
  "announcements": [
    {
      "id": "spring-2027-workshop",
      "title": "Quantum computing for professionals",
      "text": "A two-day hands-on workshop for industry teams, March 3–4, 2027.",
      "link": "https://example.org/workshop",
      "from": "2027-01-10",
      "until": "2027-03-04",
      "min_version": "0.9.5",
      "max_version": ""
    }
  ]
}
```

- **support_email**: where **Report a problem → Send by email** goes. Leave it `""` until the address
  exists; the email button then stays off and students use GitHub.
- **id**: unique and never reused. A user who closes an announcement never sees that id again.
- **title** (up to 80 characters) and **text** (up to 400): plain text, no HTML.
- **link** (optional): must start with `https://`.
- **from** / **until** (optional): dates as `YYYY-MM-DD`, both included.
- **min_version** / **max_version** (optional): only these QuantumScope versions show it (for
  example, "update to 0.9.6 for the new lab" with `"max_version": "0.9.5"`).

Only **one** announcement shows at a time: the first in the list that is current and not closed. Put
the most important first. A file that is not valid JSON shows nothing, so check it with a JSON
validator after editing. Keep it small (well under 64 KB).

Guardrails we agreed on: only our own courses, workshops and features; never third-party
advertising; one card at a time.
