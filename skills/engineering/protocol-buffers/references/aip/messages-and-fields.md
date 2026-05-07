# Messages, Fields, and Documentation

Read this when naming messages or fields, choosing field types, applying field behavior annotations, documenting protos, or using standard fields.

## Messages

- **Names:** Short, PascalCase; no prepositions (e.g. "With", "For"). Omit
  redundant adjectives if there is no contrasting type.
- **Request/response:** Request = RPC name + `Request`; response = resource for
  Get/Create/Update (and some custom), or `ListXResponse` for List, or
  `XResponse` for custom. Response usually holds the full resource unless
  partial response (AIP-157).
- **Conflict:** A message **should not** have a field with the same name as the
  message (after case normalization).

## Field names (AIP-140)

- **Case:** `lower_snake_case` in proto. No leading/trailing/adjacent
  underscores; no word starting with a number.
- **Language:** Correct American English; same concept = same name across APIs;
  avoid overloaded or overly generic names (e.g. "instance", "info", "service"
  only with clear context).
- **Repeated:** Use plural (`books`); non-repeated use singular (`book`).
  Resource names in field names use singular.
- **Prepositions:** Avoid ("for", "with", "at", "by"); e.g. `error_reason` not
  `reason_for_error`. "Per" is allowed in units (AIP-141).
- **Abbreviations:** Use common ones: `config`, `id`, `info`, `spec`, `stats`;
  for units use common abbreviations (e.g. `_km`, `_px`).
- **Adjective + noun:** Adjective before noun: `collected_items` not
  `items_collected`.
- **Verbs:** Field names **must not** be verbs or intent/action; use nouns
  (current or desired value).
- **Booleans:** Omit `is_` prefix: `disabled` not `is_disabled` (exception:
  reserved words, e.g. `is_new`).
- **URIs:** Prefer `uri`; if only URLs, use `url`. Optional prefix (e.g.
  `image_url`).
- **Display:** Human-readable name → `display_name` (no uniqueness).
  Formal/official name → `title` (no uniqueness).
- **Reserved words:** Avoid names that conflict with common language keywords.

## Field behavior (AIP-203)

Recommended when using `google.api.field_behavior` annotations. These are
helpful for documentation and code generation but not strictly required unless
the project or API Linter enforces them.

- Apply `google.api.field_behavior` on fields of messages used in requests.
  Use at least one of: `REQUIRED`, `OPTIONAL`, `OUTPUT_ONLY`. Never use
  `FIELD_BEHAVIOR_UNSPECIFIED`.
- **IDENTIFIER:** Only on the resource's `name` field (identifies resource; not
  input on Create; immutable on Update).
- **REQUIRED / OPTIONAL:** For input fields; required = must be present and
  non-empty where applicable.
- **OUTPUT_ONLY:** Response-only; server clears on input; ignore in
  update_mask.
- **INPUT_ONLY:** Request-only; not in response (rare; e.g. some TTL patterns).
- **IMMUTABLE:** Cannot be changed after creation; ignore if unchanged on
  update, error if change requested.
- **UNORDERED_LIST:** Repeated field order not guaranteed.

## Standard and special fields (AIP-148)

### Resource names and IDs

- **`name`:** Every resource **must** have `string name` as first field
  (resource name per AIP-122). Do not use `_name` suffix for other concepts
  unless covered by AIP-148.
- **`parent`:** `string parent` for the parent of a collection; used in List
  and Create requests.
- **`uid`:** Output-only `string uid` for a system-assigned unique identifier;
  should be UUID4. Annotate with `google.api.field_info` format `UUID4`
  (AIP-202) if the project uses field info annotations.

### Other names

- **`display_name`:** Mutable, user-settable, human-readable name (≤63 chars,
  no uniqueness requirement).
- **`title`:** Official/formal name (more formal variant of `display_name`).
- **`given_name` / `family_name`:** For people; **must not** use `first_name`
  or `last_name` (ordering varies by culture).

### Timestamps

- Use `google.protobuf.Timestamp`; names end in `_time` (e.g. `create_time`,
  `update_time`). Use imperative form: `publish_time` not `published_time`
  (AIP-142).
- **`create_time`:** Output-only; when the resource was created.
- **`update_time`:** Output-only; when the resource was last updated by a user.
- **`delete_time`:** Output-only; when a resource was soft deleted (empty if
  not soft deleted). Resources with soft delete (AIP-164) **should** include
  this.
- **`expire_time`:** When a resource or attribute is no longer valid.
- **`purge_time`:** When a soft-deleted resource will be permanently purged
  (AIP-164).

### Durations

- Use `google.protobuf.Duration`; e.g. `flight_duration` (AIP-142).

### Annotations

- Optional `map<string, string> annotations` for small amounts of arbitrary
  client data. **Must** use Kubernetes limits; **should** require
  dot-namespaced keys.

### State

- Use enum `State` (or `XxxState`) nested in the resource; values like
  `ACTIVE`, `SUCCEEDED`, `FAILED`, `CREATING`, `DELETING`. Field **should**
  be output-only; state changes via custom methods, not Update (AIP-216).

### Enums

- Values in `UPPER_SNAKE_CASE`; first value `{Enum}_UNSPECIFIED` (or `UNKNOWN`
  if zero). Nested in message when used only there (AIP-126).

### Quantities

- Include unit suffix (e.g. `distance_km`, `node_count`); use `_count` for
  counts, not `num_` (AIP-141). No unsigned integers.

### Etag and request ID

- **`etag`:** Optional `string etag` for optimistic concurrency; mismatch on
  update/delete → `ABORTED` (AIP-154).
- **`request_id`:** Optional `string request_id` for idempotent retries
  (AIP-155).

### Format / FieldInfo

Recommended when the project uses `google.api.field_info` annotations. These
add machine-readable format metadata but are not required unless enforced.

- Use `google.api.field_info` format (e.g. `UUID4`, `IPV4`, `IPV6`,
  `IPV4_OR_IPV6`) when applicable (AIP-202). IP address fields **should** use
  type `string` and the name `ip_address` or suffix `_ip_address`.

## Pagination (List)

- Request: `int32 page_size` (optional; document default and max; coerce over
  max; error on negative), `string page_token`.
- Response: repeated items + `string next_page_token` (set only when there is a
  next page).
- Optional `int32 total_size` or `int64 total_size` (may be an estimate;
  document if so; reflects count after filtering).

## Documentation (AIP-192)

- Public comments **must** be on every component (service, method, message,
  field, enum, enum value). Always use **leading comments** (above the
  element), never trailing or inline comments.
- **Style:** Grammatically correct American English. First sentence **should**
  omit the subject and use third-person present tense (e.g.
  `// Creates a book under the given publisher.`).
- **Formatting:** **Must** use CommonMark. No headings or tables in comments.
  No raw HTML. No ASCII art. Use `code font` for field/method names and
  literals.
- **Resource name patterns:** Document with `// Format: publishers/{publisher}/books/{book}`.
- **Cross-references:** Link to other components with fully-qualified names
  (e.g. `[Book][google.example.v1.Book]`) or scope-relative references.
- **External links:** **Must** use absolute URLs including protocol.
- **Deprecations:** Set `deprecated` option to `true` **and** start the
  comment with `"Deprecated: "` plus alternatives or reason.
- **Internal comments:** Wrap non-public content in `(--` and `--)`.
  Non-public links, `TODO`/`FIXME` **must** be marked internal.
- **Precedent violations:** Document deviations with comment prefixed
  `aip.dev/not-precedent` and justify per AIP-200.

## Errors

- Return `google.rpc.Status` with `google.rpc.Code`. Include `ErrorInfo` in
  `details` with machine-readable `reason` (UPPER_SNAKE_CASE, ≤63 chars).
  Message: developer-facing, English, brief and actionable; dynamic parts in
  `details` (AIP-193).
