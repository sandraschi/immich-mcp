# Immich MCP — User Tutorial

Welcome! This guide teaches you — a human using Claude, Cursor, or another MCP
host — how to get the most out of the Immich MCP server. It is written as a set
of friendly, worked examples. You do not need to read it cover to cover: jump to
the task that matches what you want to do, copy the flow, and adapt it to your
library.

Immich is a self-hosted photo manager (like Google Photos, but yours). The MCP
server is the bridge between your AI assistant and that library: search, albums,
people, OCR, libraries, backup, multi-user. The assistant does the heavy lifting;
you provide intent and confirmation for destructive steps.

---

## Chapter 1 — Before you start

### 1.1 What you need

1. A running Immich server. If you do not have one, install it (Docker Compose is
   the standard way; Immich's docs cover it) and open it in your browser at
   something like `http://localhost:2283`.
2. An API key. In Immich, click your avatar → Administration → API Keys →
   New API Key. Copy it.
3. The server configured. In the immich-mcp repo directory, copy `.env.example`
   to `.env` and fill in:

   ```
   IMMICH_SERVER_URL=http://localhost:2283
   IMMICH_API_KEY=your_key_here
   ```

4. Start the server:

   ```
   uv sync
   uv run immich-mcp
   ```

   (or `just serve` / your host's MCP configuration — see INSTALL.md).

### 1.2 Sanity check

Ask your assistant: "Check the Immich server health." You should get back the
server version, database status, and response time. If instead you see an error,
look at Chapter 8 (Troubleshooting) — 90% of first-run problems are a wrong URL
or a missing key.

### 1.3 The five-second mental model

- **Search first.** There is no "show me everything" — you always search.
- **Albums are the organizing unit.** Photos are grouped into albums you create.
- **People are clusters.** Immich detects faces; you name them.
- **OCR reads text in images.** Receipts, screenshots, documents are searchable.
- **Libraries are external folders.** Connect a disk folder to Immich.
- **Everything destructive needs your OK.** Trash is safe; permanent delete is not.

---

## Chapter 2 — Finding your photos

### 2.1 The everyday search

You: "Find the photos from our trip to Prague."

The assistant will run a semantic search — it understands the *content* of the
photos, not just filenames:

```
search_photos(query="Prague trip", search_type="smart", limit=50)
```

You get back a list with filenames, dates, and a relevance score. If the first
query is too broad, refine it: "only the castle ones" or "the ones with the red
umbrella" — semantic search handles that.

### 2.2 Searching by what the image *says*

You: "Find the receipt from the electronics store."

That is OCR search — text inside images:

```
search_photos(query="receipt electronics", search_type="ocr", limit=20)
```

This works because Immich extracts text from every image. Tip: search for a
fragment you remember — a store name, an order number, a word — rather than the
whole sentence.

To read a specific image's text:

```
get_ocr_data(asset_id="<id from the results>")
```

You get the full text plus where each word sits in the image (bounding boxes and
confidence). Perfect for "what does this say / where is it in the image".

### 2.3 Searching by camera or date

You: "All photos taken with the Nikon on ISO 800 last summer."

```
search_photos(query="Nikon", search_type="metadata", limit=100)
```

Metadata search covers EXIF fields: camera make/model, ISO, lens, date, GPS
location, tags. Combine with the date in your follow-up question — the assistant
can filter the results by date for you.

### 2.4 The full dossier on one photo

You: "What do we know about this photo?" (pasting an asset id or a filename)

```
get_photo_info(asset_id="550e8400-e29b-41d4-a716-446655440000")
```

This returns the complete EXIF: capture date, GPS coordinates, camera body,
lens, focal length, ISO, shutter, file size, checksum, AI tags, people, albums.
This is the tool for "when was this taken", "where was this taken", or "which
camera took this".

### 2.5 Downloading an original

You: "Save this photo to my temp folder so I can use it locally."

```
download_photo_to_temp(photo_id="<id>")
```

The server downloads the original file and returns the local path. Use this
before EXIF syncing or any other local-file workflow.

---

## Chapter 3 — Uploading and organizing

### 3.1 Uploading a batch

You: "Upload everything in D:/Camera Dump."

```
upload_photos(file_paths=["D:/Camera Dump/img_001.jpg", "D:/Camera Dump/img_002.jpg", "..."])
```

Missing files are skipped and reported; duplicates are detected (if you re-upload
something Immich already has, it tells you — no duplicates in your library).
Optionally send them straight into an album:

```
upload_photos(file_paths=[...], album_name="Camera Dump 2026")
```

### 3.2 Organizing a trip into an album

After a successful search, ask: "Put all of these into an album called 'Prague
2026'." The assistant creates the album and adds the photos:

```
create_album(name="Prague 2026", description="Trip photos", asset_ids=[...])
add_to_album(album_id="<id>", asset_ids=[...])
```

Or let the server do the dating for you:

```
organize_photos_by_date(asset_ids=[...], album_name="Prague 2026")
```

This creates a date-grouped album ("Prague 2026" with date ranges) — great for
long trips.

### 3.3 Visibility: archive, hide, lock

You: "Archive these so they don't clutter the timeline" or "Lock this one so it
can't be edited."

```
update_asset_visibility(asset_id="<id>", visibility="archive")
update_asset_visibility(asset_id="<id>", visibility="locked")
```

The valid values are exactly: `archive` (out of the timeline), `timeline`
(normal), `hidden` (out of search and timeline), `locked` (read-only). The
assistant will explain what each does before applying if you ask.

### 3.4 Editing a photo (crop / rotate / mirror)

You: "Rotate this portrait 90 degrees."

```
edit_photo(asset_id="<id>", operation="rotate", parameters={"angle": 90})
```

Supported operations: `crop`, `rotate`, `mirror`. The edit is applied through
Immich's native edit pipeline, so the original is preserved.

---

## Chapter 4 — Albums

### 4.1 Seeing what you have

```
list_albums(include_stats=True)
```

Returns every album with its photo/video counts and sizes. Always do this first
before creating or adding — maybe the album already exists.

### 4.2 Creating and filling

```
create_album(name="Family 2026", description="The whole clan")
add_to_album(album_id="<id>", asset_ids=[...])
```

### 4.3 Sharing a collection

You: "Send a link so friends can see the wedding photos."

```
share_album(album_id="<id>", expires_at="2026-12-31T23:59:59", allow_download=True)
```

Options: `allow_download` (visitors can download originals), `allow_upload`
(visitors can add photos — great for events), `show_metadata` (show EXIF info),
and an optional `expires_at` for a time-limited link.

---

## Chapter 5 — People and faces

### 5.1 Kicking off face detection

You: "Detect people in these photos."

```
detect_people(asset_ids=[...])
```

This queues the real Immich job (`refresh-faces`). Detection runs in the
background on the Immich side; the tool honestly reports that the job was
submitted, not that faces exist yet.

### 5.2 Naming a person

Once clusters exist, Immich exposes detected persons. You name them:

```
tag_person(person_id="<id>", name="Grandma")
```

You can restrict which face samples get the name with `face_asset_ids` — useful
when a person appears in group photos.

### 5.3 Collecting all photos of someone

```
search_by_person(person_name="Grandma", limit=100, include_metadata=True)
```

Exact match on the assigned name. Perfect for birthday albums, gift prep, or
"show me every photo of Benny the dog".

---

## Chapter 6 — Libraries (external folders)

Libraries connect folders on disk to Immich so files can be watched and imported
automatically.

### 6.1 Listing and inspecting

```
list_libraries()
get_library_info(library_id="<id>")
```

Shows import paths, asset counts, and scan state.

### 6.2 Creating a library

```
create_library(name="Archive Disk", import_paths=["/mnt/archive/photos"], owner="sandra")
```

The server resolves the owner (defaults to the current user) and the required
ownerId automatically.

### 6.3 Scanning

```
scan_library(library_id="<id>")
```

Triggers an import scan of the configured paths. New files appear in Immich after
the scan completes.

### 6.4 Per-user visibility

In multi-user setups:

```
get_user_libraries(username="steve")
```

Shows which libraries a user can access without you permanently switching
accounts.

---

## Chapter 7 — Storage, backup, and maintenance

### 7.1 How much space am I using?

```
get_storage_info()
```

Returns used/available/total bytes, usage percentage, photo count, video count,
user count, album count. The dashboard's four KPI cards read from this.

### 7.2 Backing up an album locally

You: "Back up the whole 'Prague 2026' album to D:/Backups."

```
backup_photos(backup_path="D:/Backups", album_ids=["<id>"], include_metadata=True)
```

Downloads the originals (plus metadata sidecars if you ask) into the folder,
creating it if needed. Great before deleting anything from the server, or for an
offline archive.

### 7.3 Writing metadata back to files

```
sync_metadata_to_exif(photo_id="<id>", local_path="D:/Backups/img_001.jpg")
```

Writes the Immich-side metadata (tags, dates, GPS) into the local file's EXIF —
useful after a backup if you want the files to be self-describing.

### 7.4 Finding duplicates

```
detect_similar_photos()
```

Queues Immich's similarity job and reports submission. Run it occasionally to
spot near-duplicates (same photo exported twice, different names).

### 7.5 Server health and shutdown

```
server_health()          # version, DB/Redis, uptime, response time
immich_shutdown(confirm=True)   # stop the server when you are done
```

---

## Chapter 8 — Troubleshooting

### 8.1 "Cannot connect to Immich"

The classic. The server cannot reach your Immich instance.

1. Check the URL: `IMMICH_SERVER_URL` must include the scheme and port —
   `http://localhost:2283`, not `localhost:2283` and not `http://localhost:2283/api`.
2. Is Immich actually running? Open the URL in a browser.
3. Firewall? If Immich is on another machine, allow the port.

The error message tells you which of these it suspects ("connection refused"
vs "timeout" vs "network").

### 8.2 "Immich rejected the API key"

1. In Immich: Administration → API Keys → generate a new key.
2. Update `.env` (`IMMICH_API_KEY`, or the matching entry in `IMMICH_USERS`).
3. Restart the server.

### 8.3 Searches come back empty

- **Smart search empty**: the ML/CLIP pipeline is off. Enable machine learning in
  Immich's admin settings, wait for jobs to finish, search again. Meanwhile, use
  `metadata` or `ocr` search — they do not need ML.
- **OCR search empty**: either the images genuinely have no text, or OCR models
  are not installed on the server. Try `get_ocr_data` on a screenshot to test.
- **Everything empty but the library is full**: make sure you searched with a
  real term — there is no "list all" endpoint by design.

### 8.4 "Asset not found"

The id is stale (deleted, or from an old search). Re-run a search to get a fresh
id. This also happens when you switch users — each user sees their own library.

### 8.5 Uploads report duplicates

That is not an error — Immich already has those files (same checksum). The report
tells you which; leave them or delete the local copies.

### 8.6 OCR says empty on a document

The image may be a scan with embedded text layers instead of pixels — Immich's
OCR reads pixels. Export as PNG/JPG and retry.

### 8.7 The webapp dashboard shows errors

The webapp reads `/api/v1/system/storage` and `/api/v1/system/health`. If the
cards show a connection error while MCP tools work, check the webapp's backend
port (10839) and that the backend is running with `start.ps1`. If the Chat page
says "No local LLM detected", start Ollama (port 11434) or LM Studio (port 1234)
— the app auto-detects them.

---

## Chapter 9 — Multi-user setups

Configure users in `.env`:

```
IMMICH_USERS=sandra:key1:admin:Primary,steve:key2:user:Secondary
IMMICH_ACTIVE_USER=sandra
```

Workflow:

1. `list_users()` — who is configured?
2. `switch_user("steve")` — act as Steve (all calls use Steve's key).
3. `get_user_libraries("steve")` — what can Steve see?
4. `switch_user("sandra")` — switch back when done.

Roles: `admin` (full), `user` (own libraries), `shared` (limited). Role-based
capabilities are reported by `get_current_user()`.

---

## Chapter 10 — Agentic workflows

For multi-step goals, let the assistant plan and execute autonomously:

```
agentic_immich_workflow(workflow_prompt="Organize all 2025 photos into monthly albums")
```

The assistant uses MCP sampling to plan the steps and calls the tools itself.
You stay in the loop for confirmations. There are two companions:

- `intelligent_photo_processing(photos, processing_goal, available_operations)` —
  batch decisions over a photo set ("which of these are keepers?").
- `conversational_immich_assistant(user_query)` — a chatty, planning-oriented
  answer about what to do with your library.

These require a host that supports MCP sampling (Claude Desktop, Cursor with
sampling enabled). Without sampling they return a clear error telling you so.

---

## Chapter 11 — Pro tips

1. **Date ranges are your friend.** "Photos from March" → metadata search + your
   follow-up filter. The assistant keeps the thread, so narrow down iteratively.
2. **Name your people once.** `tag_person` pays off forever — every future
   `search_by_person` gets better.
3. **Use albums as project buckets.** A "2026 Tax Receipts" album fed by OCR
   searches makes April easy.
4. **Backup before big deletions.** One `backup_photos` call, then delete with
   peace of mind.
5. **Share links expire.** Always set `expires_at` for anything semi-sensitive.
6. **The dashboard is a mirror.** The webapp (ports 10838/10839) shows the same
   data the agent sees — good for a human overview while the agent works.
7. **Ask for the Prefab card.** In hosts with MCP Apps, `show_server_health_prefab`
   renders a beautiful health card in the chat.
8. **Combine search types.** "Find the receipt (OCR) from the Nikon (metadata)
   taken in March" — the assistant can run both and intersect.

---

## Chapter 12 — Privacy and safety notes

- Everything stays on your hardware unless you share an album link — Immich is
  self-hosted, and the MCP server talks only to your instance.
- Share links are public URLs while valid — treat `expires_at` as mandatory for
  anything personal.
- Permanent deletion is irreversible (no trash). Confirm carefully.
- The API key in `.env` grants full access to the configured user — never commit
  `.env` to git, never paste it into a chat with third parties.
- Backups written with `backup_photos` are ordinary files on disk — protect the
  backup folder like you would the original library.

---

## Closing words

That is the whole tour. The golden rule: **search, then organize, then share** —
and confirm anything destructive. Every tool in this server returns both a
human-friendly summary and structured data, so whether you are chatting with
Claude or driving it from a script, you always know what happened and what to do
next. Happy organizing!

---

## Chapter 13 — Walkthrough: the complete "trip album" session

This is the single most common real-world session, end to end, exactly as you
would drive it with the assistant.

**Step 1 — Find the photos.** "Find photos from our Prague weekend in March."

The assistant runs a smart search, then a metadata search for March, and merges
the results. You review the list (filenames, dates, scores) and say "yes, those
about 60".

**Step 2 — Create the album.** "Make an album 'Prague March 2026' and put them
in it."

One `create_album` + one `add_to_album`. The assistant confirms counts.

**Step 3 — Add the stragglers.** "Also include the ones from the airport on the
way home." The assistant searches "Prague airport March", you approve, one more
`add_to_album`.

**Step 4 — Name the people.** "Tag us in the album." The assistant runs
`detect_people` on the album's assets (job queued), and when clusters are ready,
you name them: `tag_person` twice, then `search_by_person` to verify all photos
of each person are present.

**Step 5 — Share with family.** "Share it, allow downloads, expire in a month."

`share_album(expires_at=..., allow_download=True)` → the assistant hands you the
link.

**Step 6 — Back it up.** "Also back the album up to D:/Backups/Prague."

`backup_photos(backup_path="D:/Backups/Prague", album_ids=[...], include_metadata=True)`
→ count + size + elapsed time reported.

Total: six conversational turns, four tools, one shared link, one local backup.
That is the power of the server: intent in, organized library out.

---

## Chapter 14 — Walkthrough: the tax-season OCR hunt

Every year: find every receipt and invoice in the library.

1. "Find all receipts from 2025" → `search_photos(query="receipt 2025", search_type="ocr", limit=100)`.
2. Review the hits; for a few, `get_ocr_data` to confirm the text (amount,
   vendor, date).
3. "Create an album '2025 Receipts' and add these." → `create_album` +
   `add_to_album`.
4. Repeat with more terms: "invoice", "Rechnung" (German libraries), "order
   confirmation", the tax office's name. Each pass appends to the album.
5. At the end, `backup_photos` the album → you have a tidy folder for your
   accountant.

Tip: OCR search matches text fragments — search for the vendor or the word
"invoice", not the whole document. Short distinctive strings beat long phrases.

---

## Chapter 15 — Walkthrough: cleaning up a camera dump

Your camera dumped 2000 files, many of them blurry or duplicates.

1. `upload_photos` the whole folder (duplicates auto-reported).
2. "Which photos are similar?" → `detect_similar_photos()` queues the similarity
   job; when it finishes, the assistant can list candidate duplicates.
3. For each candidate pair: `get_photo_info` on both, compare resolution and
   dates, and let you decide. Keep the highest-resolution copy.
4. "Trash these" → `delete_photos(asset_ids=[...], move_to_trash=True)` — safe,
   recoverable.
5. After a week, if you are sure: empty the trash through the Immich UI (the API
   contract deliberately keeps trash empty-recovery in Immich's hands).

---

## Chapter 16 — Walkthrough: a full backup day

You want an offline archive of everything.

1. `get_storage_info()` — how big is the library? (Photos + videos count.)
2. Decide scope with the user: everything, or by album? `list_albums` shows the
   candidates.
3. `backup_photos(backup_path="F:/ImmichArchive", album_ids=[...], include_metadata=True)`
   — run it (large jobs stream; the assistant reports progress).
4. Spot-check: `download_photo_to_temp` + `sync_metadata_to_exif` on a sample to
   confirm metadata sidecars are complete.
5. Log the result (count, size, date) in the chat so there is a record.

---

## Chapter 17 — Walkthrough: multi-user audit

You administer a family Immich with three accounts.

1. `list_users()` — see all configured users and who is active.
2. `get_current_user()` — confirm your own role and capabilities.
3. For each other user: `get_user_libraries("steve")` — what libraries does Steve
   have access to? Any surprises?
4. `switch_user("steve")` → `list_libraries()` — verify from Steve's perspective
   (his key's permissions). `switch_user("sandra")` to return.
5. Fix configuration in `.env` if a user is missing a library, restart, re-check.

---

## Chapter 18 — Walkthrough: building a "People of the year" album

A delightful end-of-year task.

1. `list_users()` not needed — this is about detected people, not accounts.
2. "Who have I tagged?" → the assistant runs `search_by_person` for each known
   name (start with 2-3 names you remember).
3. For untagged clusters: `detect_people` + review, then `tag_person`.
4. Create "People of 2026" and `add_to_album` the union of results.
5. Share with `expires_at` if it goes to family.

---

## Chapter 19 — Combining search types (advanced)

The strongest queries combine two search modes. The assistant can run both and
intersect the results. Example:

"Find the car-rental receipt from Italy — it was taken with my phone (iPhone),
in June."

- OCR search: `search_photos(query="rental car", search_type="ocr", limit=50)`
  finds text-bearing images.
- Metadata search: `search_photos(query="iPhone", search_type="metadata", limit=50)`
  finds camera-scoped images.
- Metadata by date: filter June via the assistant's follow-up.
- Intersection → usually exactly the receipt.

If you get zero intersections, widen one leg (drop the camera filter, or the
date) — the assistant will tell you which leg to relax.

---

## Chapter 20 — Working with the webapp

The server ships a full webapp (frontend port 10838, backend 10839; start with
`start.ps1`).

- **Dashboard** — KPI cards: total assets, library size, system health, API
  bridge latency. These read live from the server.
- **Photos / Albums / People / Map / Libraries** — visual browsers over the same
  data the MCP tools return. The Map page renders GPS-tagged photos on a Leaflet
  map.
- **Chat** — a skill-first chat page with four personalities (Photo Curator and
  friends), conversation history in localStorage, export to .txt, and example
  prompts. It talks to your local LLM (Ollama/LM Studio auto-detected).
- **Tools** — the live MCP tool list; **Logger** — a ring-buffer log viewer;
  **Settings** — users, LLM providers and models; **Help** — this guide's quick
  reference.

You can drive the same operations from the webapp or from the agent — they share
the one backend.

---

## Chapter 21 — Frequently asked questions

**Q: Does this work with Immich v3?**
A: Yes. The API contracts were verified against v2.7.5, v3.0.3, and v3.1.0
OpenAPI specs. A few v3-only behaviors are handled automatically (e.g. the
integer `duration` field on uploads).

**Q: My OCR searches are slow.**
A: OCR search uses a full-text index. Smart (CLIP) search uses a vector index and
is faster. Prefer smart unless you specifically need text-in-image.

**Q: Can I search videos?**
A: Assets include both images and videos; search and albums cover both. Thumbnails
and metadata work for videos; OCR obviously does not (no text layer).

**Q: How many photos can one search return?**
A: Default 50, capped at 200 per call. Use targeted queries rather than huge
pages — and remember there is no "list all".

**Q: I switched users and now things look empty.**
A: Each user sees their own library. Use `switch_user` to return, or
`get_user_libraries` to inspect without switching.

**Q: The share link does not work.**
A: Links are only valid while the share exists and before `expires_at`. Re-share
with `share_album` if it expired.

**Q: Where does the downloaded temp photo go?**
A: To a temp directory the server manages; `download_photo_to_temp` returns the
exact path. It is a cache — copy the file if you need it long-term.

**Q: Backups are slow for big albums.**
A: They stream; thousands of photos take minutes. Start with one album to gauge
speed, and keep the backup disk local to the server for maximum throughput.

---

## Chapter 22 — Reference card (print this)

```
SEARCH      search_photos(query, search_type=smart|ocr|metadata|filename, limit)
DETAIL      get_photo_info(asset_id) | get_ocr_data(asset_id)
DOWNLOAD    download_photo_to_temp(photo_id)
UPLOAD      upload_photos(file_paths, album_name?, auto_organize?)
ORGANIZE    organize_photos_by_date(asset_ids, album_name?)
VISIBILITY  update_asset_visibility(asset_id, archive|timeline|hidden|locked)
EDIT        edit_photo(asset_id, crop|rotate|mirror, parameters?)
DELETE      delete_photos(asset_ids, move_to_trash=True)
ALBUMS      list_albums | create_album | add_to_album | share_album
PEOPLE      detect_people | tag_person | search_by_person
LIBRARIES   list_libraries | get_library_info | create_library | scan_library
USERS       list_users | switch_user | get_current_user | get_user_libraries
STORAGE     get_storage_info | backup_photos | sync_metadata_to_exif
SYSTEM      server_health | immich_help | immich_shutdown | detect_similar_photos
AGENTIC     agentic_immich_workflow | intelligent_photo_processing
PREFAB      show_server_health_prefab
```

Keep this card next to your prompts and you will never guess a tool name again.

---

## Chapter 23 — Wiring the server into your host

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "immich": {
      "command": "uv",
      "args": ["run", "--directory", "D:/Dev/repos/immich-mcp", "python", "-m", "immich_mcp"]
    }
  }
}
```

**Cursor / Windsurf** — same shape in the MCP settings panel, or a `.mcp.json`
in the project root with the identical entry.

**opencode** — add to `opencode.json`:

```json
{
  "mcp": {
    "immich": {
      "type": "local",
      "command": ["uv", "run", "--directory", "D:/Dev/repos/immich-mcp", "python", "-m", "immich_mcp"]
    }
  }
}
```

**HTTP mode** (for the webapp or remote use):

```
MCP_TRANSPORT=http MCP_PORT=10839 MCP_HOST=127.0.0.1 uv run python -m immich_mcp
```

The MCP endpoint is `http://127.0.0.1:10839/mcp`; the REST API lives under
`/api/v1` on the same port.

After wiring, restart your host and confirm the tool list loads (33+ tools). If
the tool list is empty, the server failed to start — check `.env` values and the
host log; the error message names the missing variable.

---

## Chapter 24 — Ten session recipes (copy-paste starters)

1. **Trip album**: "Find photos from <place> <time>, album them, share with
   expiry, back them up."
2. **Receipt hunt**: "Find all <vendor> receipts this year (OCR), album them."
3. **Face cleanup**: "Detect people, tag <names>, verify with search_by_person."
4. **Duplicate sweep**: "Find similar photos, compare pairs, trash the
   low-res ones (to trash, not permanent)."
5. **Archive day**: "Back up <album list> to <disk>, include metadata, report
   sizes."
6. **Family library audit**: "List users, check each one's libraries, verify
   from their key."
7. **Camera journal**: "Show me everything taken with <camera> in <month>."
8. **EXIF repair**: "Sync metadata to EXIF for these downloaded files."
9. **Event share**: "Create album, upload <folder>, share with upload allowed,
   expire in 2 weeks."
10. **Year in review**: "Build 'People of <year>' from all tagged people."

Each recipe is 1-3 turns with the assistant. Paste the intent, review the
confirmations, done.

---

That completes the tutorial. Start with Chapter 2 if you only remember one
thing: search, then organize, then share — and confirm anything destructive.

## Chapter 25 — Understanding what the assistant sees

When you chat with the assistant through an MCP host, it sees your photo library
exactly as the API exposes it: assets with ids, filenames, dates, EXIF, smart
tags, OCR text, album memberships, person clusters, library paths, storage
totals. It does not see the raw image pixels unless OCR or smart-search text is
available. Practically this means:

- "Show me the photo" becomes a search + thumbnail or a downloaded temp file.
- "Is this blurry?" is answered from EXIF (shutter speed, ISO) and smart info,
  not by looking at pixels — a human check of the actual image is the ground
  truth when it matters.
- Album and person names are the strongest anchors: they are human-readable
  labels the assistant can reason about directly.
- The assistant can chain anything: search results feed albums, albums feed
  backups, backups feed EXIF sync, and so on. Keep the ids flowing from one
  step to the next and complex pipelines become one-liners.

One more tip: when you are unsure which tool fits, just describe the goal. The
assistant picks the tool; if it picks wrong, the error message it gets is
structured enough to self-correct on the next try. That is the design: the
server makes every failure explainable and every success reusable.
