# rendering/

`render.sh` is the **only** supported way to render in this project.

```bash
bash rendering/render.sh --quality draft \
  --composition index.html --output output/factory-test-draft.mp4

bash rendering/render.sh --quality standard \
  --composition index.html --output output/factory-test.mp4
```

What it does, every time:

1. Sets `TMPDIR` and `HYPERFRAMES_EXTRACT_CACHE_DIR` inside the workspace
   (`.cache-tmp/tmp`, `.cache-tmp/frames`) — never `/tmp` (512 MB tmpfs).
2. Refuses to render with less than 500 MB of free memory.
3. Takes a lock (`.cache-tmp/render.lock`) — never two heavy renders at once.
4. For the factory test, renders draft first when no draft exists.
5. Calls `npx hyperframes render` with the requested quality.

Never call `npx hyperframes render` directly. If a render fails, read its
log first: a failure in the draft usually means the composition is broken
(run `npx hyperframes check`), a failure at the end usually means disk or
memory (run `bash scripts/check-env.sh`).
