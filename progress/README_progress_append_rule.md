# Progress Log Append Rule

When a Ralph harness run modifies `progress/progress.txt`, the new iteration entry must be appended to the absolute end of the file.

The newest entry must be the final content in the file.

Do not insert a new progress entry above older entries.

Do not keep a footer after the newest entry.

If this rule is violated, the harness may fail with an error similar to:

```text
ERROR: progress/progress.txt changed but end-of-file tail did not change.
Progress entries must be appended at EOF.
```
