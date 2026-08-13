# Production Queue

Recommended render queue schema:

```text
job_id
shot_spec_uri
renderer_manifest_uri
priority
profile
status
attempt
artifact_uri
qa_status
qa_failures
retake_parent_job
```

Profiles:
- draft
- final
- retake
- control-heavy
- audio-driven

Flow:

```text
compile 20–100 shots on CPU
↓
draft render
↓
automatic/manual QA
↓
final only accepted shots
↓
Retake failed intervals
↓
store artifact + renderer manifest
```
