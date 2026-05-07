# RPCs and Methods

Read this when defining RPCs, configuring HTTP transcoding, or choosing between standard and custom methods.

## HTTP and transcoding

- Every RPC **must** have an HTTP mapping via `google.api.http` (except
  bi-directional streaming, which should have a non-streaming alternative if
  possible).
- **Verbs:** Use `get`, `post`, `patch`, or `delete` as prescribed; **should
  not** use `put` or `custom`.
- **URI:** Use `{field=path/*}` for variables; use `*` for one segment (no
  `/`), `**` only if needed for path segments. For Update, use nested field in
  path (e.g. `{book.name=...}`).
- **Body:** No `body` for GET/DELETE. For Create/Update, `body` must point to
  the resource field; must not be nested, a URI param, or repeated. Prefer not
  using `json_name` except for compatibility.
- **Method signatures:** Use `google.api.method_signature` as specified per
  method type below.

## Standard methods

See [naming-and-methods.md](naming-and-methods.md) for the standard-methods table.

- **Get (AIP-131):** Request has `name` (required, resource reference). URI
  single variable for resource; `method_signature = "name"`. Response is the
  resource (fully populated unless partial response per AIP-157).
- **List (AIP-132):** Request has `parent` (required when not top-level),
  `page_size` (int32), `page_token` (string); optional `filter` (AIP-160),
  `order_by`. Response has repeated resource field + `next_page_token`;
  optional `total_size` (may be an estimate; document if so). Pagination is
  mandatory from the start (AIP-158).
  `method_signature = "parent"` (or `""` for top-level).
  - **Ordering:** Optional `string order_by`. Values are comma-separated field
    names; append `" desc"` for descending (e.g. `"foo desc, bar"`). Subfields
    use `.` (e.g. `address.street`).
  - **Soft-deleted resources:** APIs with soft delete **should** include
    `bool show_deleted` in the request; soft-deleted resources **should not**
    appear in results by default.
- **Create (AIP-133):** Request has `parent`, `{resource}_id`, and resource
  field (body). Resource `name` ignored on input.
  `method_signature = "parent,book,book_id"` (or without `_id` if optional).
  Management plane **must** allow user-specified ID; data plane **should**.
- **Update (AIP-134):** Request has resource field (with `name`) +
  `google.protobuf.FieldMask update_mask`. URI uses `{resource.name=...}`.
  Support partial update (PATCH). Omitted mask = all populated fields. Support
  `*` for full replacement with documented caveats. State fields **must not**
  be writable in Update (use custom methods). Optional `allow_missing` for
  upsert when using client-assigned names. Optional `etag` for conditional
  update (AIP-154).
- **Delete (AIP-135):** Request has `name`. Response is `google.protobuf.Empty`
  (hard delete), the resource (soft delete per AIP-164), or LRO. Optional
  `force` for cascading delete; optional `etag` for conditional delete;
  optional `allow_missing` for no-op when missing. Child resources present
  without `force` → `FAILED_PRECONDITION`.

## Custom methods

- Use only when standard methods do not fit; prefer standard methods.
- **Name:** Verb + noun, UpperCamelCase (e.g. `ArchiveBook`). **Must not**
  include prepositions or "Async"; **may** use `LongRunning` suffix. **Should
  not** reuse standard verbs (Get, List, Create, Update, Delete).
- **HTTP:** GET for read-only; POST for side effects. URI must include
  `:customVerb` in camelCase (e.g. `:archive`).
- **Body:** Prefer `body: "*"`.
- **Request/response:** `{RpcName}Request` and `{RpcName}Response` (or return
  the resource when operating on one resource).
- **Resource-based:** Single resource → `name` in path. Collection-based →
  `parent` in path + literal collection segment. Stateless → scope field (e.g.
  `project`) in path; verb after `:` (e.g. `:translateText`).

## Long-running operations (LRO)

- For operations that take significant time, return
  `google.longrunning.Operation` with `google.longrunning.operation_info`
  (`response_type`, `metadata_type`). Implement the standard Operations
  service; do not define a custom LRO interface.
