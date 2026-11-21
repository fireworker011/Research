---
id: example-confirm
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: read-page
    mode: read-only
    summary: Read the current value on the page
  - id: save-value
    mode: irreversible
    kind: save
    summary: Save the single field named in this order
---

Read the current value first.
Before saving, write the confirm JSON and wait.
Field: {{FIELD}}
New value: {{VALUE}}
If a login page or 2FA appears, stop and report the URL.
