# Dev workflow

Public-facing FastAPI app over `bolsa-core`, which carries the actual
fetching/parsing/scoring logic and its own `WORKFLOW.md`. If you're
touching a fetcher, the Lattes parser, OpenAlex, scoring or the report
builder itself, go there -- this repo should only ever call into it.

This repo has no login and is told nothing is stored beyond the request
(see `README.md`), which makes every endpoint in `web/routes.py` a
stronger trust boundary than `bolsa-skill`'s CLI: anyone on the internet
can hit it, with arbitrary uploaded files.

1. **Plan before coding.** For a new endpoint, write down the request/
   response shape (`web/schemas.py`) before the route body.

2. **Test first.**

   ```
   uv run pytest
   ```

3. **Security/trust check -- this is the main point of this file.**
   Before merging any change to `web/routes.py` or `web/app.py`:
   - uploads stay bounded: `MAX_UPLOAD_BYTES` and `ALLOWED_SUFFIXES`
     (`.xml`/`.pdf`) are enforced before the file touches
     `parse_lattes_xml`/`parse_lattes_pdf` -- never widen these without
     re-checking both parsers handle hostile/oversized input gracefully
   - uploaded files are read into `tempfile`, never written under a
     path derived from the client-supplied filename
   - every request/response goes through a Pydantic model in
     `web/schemas.py`, never raw dict access on `request.json()`/form
     fields
   - don't add confidence/validation layers on user-supplied IDs
     (ORCID etc.) -- see memory `feedback_trust_input_dont_overvalidate`
   - no data from a request is persisted (logged with PII, written to
     disk outside the temp upload, etc.) -- the "nothing is stored" claim
     in the README has to stay true

4. **After a `bolsa-core` change lands**, re-pin it here the same way as
   in `bolsa-skill`:

   ```
   uv lock --upgrade-package bolsa-core
   uv sync
   uv run pytest
   ```

5. **Review the diff yourself** (or via `/code-review`), with the
   security checklist above as the focus -- correctness bugs here are
   usually also trust-boundary bugs.

6. **Keep docs in sync.** If an endpoint's shape changes, update
   `README.md`'s endpoint list in the same change.
