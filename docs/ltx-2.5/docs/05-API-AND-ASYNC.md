# API Production Pattern

Official current API domain:
https://api.ltx.io

Docs:
https://docs.ltx.io/welcome

## For development
Use synchronous endpoints for short interactive tests.

## For production
Use asynchronous endpoints:

```text
submit
↓
job_id
↓
poll
↓
result URI
↓
download/store
↓
QA
```

## Adapter interface

```python
class VideoRenderer:
    def submit(self, shot_spec): ...
    def status(self, job_id): ...
    def fetch(self, job_id): ...
```

Implementations:

```text
LTX25ApiRenderer
LTX25ComfyRenderer
LTX25LocalRenderer
```

The rest of the application only sees:
- RenderJob
- RenderStatus
- RenderArtifact
