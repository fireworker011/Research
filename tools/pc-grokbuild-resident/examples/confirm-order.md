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
Before saving, write queue/confirm/example-confirm.json in the steps shape below, then wait.
Field: {{FIELD}}
New value: {{VALUE}}
If a login page or 2FA appears, stop and report the URL.

確認ファイルの形（実機で書かれる形）:

```json
{
  "job_id": "example-confirm",
  "steps": [
    {
      "step_id": "save-value",
      "kind": "save",
      "target_url": "https://example.com/page",
      "changes": [
        {"field": "{{FIELD}}", "before": "current value", "after": "{{VALUE}}"}
      ]
    }
  ]
}
```

常駐は、この `steps` 配列と、直下に `step_id` がある平らな1件の両方を読みます。書くときは `steps` にします。
