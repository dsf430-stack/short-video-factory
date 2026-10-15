# Actions request bridge

Submit one uniquely named JSON file per commit to this directory on main. The GitHub connector's file commit triggers actions-request.yml, which uses the job's short-lived GITHUB_TOKEN with actions:write to dispatch an existing workflow in this repository.

Example:
```json
{
  "workflow": "voice-068.yml",
  "ref": "main",
  "inputs": {
    "narration": "繁體中文旁白",
    "filename": "unique-output-name"
  }
}
```

Use only when the user has authorized the target operation. Read the actual workflow inputs first. The target workflow must support workflow_dispatch and exist on the default branch; select an existing ref. This bridge does not turn arbitrary scripts into video workflows.

Submit exactly one new JSON per commit, with a unique filename for each request. Do not submit secrets. Existing request files are not replayed. A request job succeeding means dispatch was accepted; verify the separate target run and its artifacts before reporting the requested work as complete.

The bridge itself accepts request_id for an isolated verification that a new workflow_dispatch run started. No publication or video rendering happens during verification.
