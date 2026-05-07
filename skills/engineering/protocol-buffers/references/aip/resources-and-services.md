# Services, Resources, and Resource Names

Read this when defining services, designing resource hierarchies, choosing resource names, or adding resource annotations.

## Services (interfaces)

- **Interface name:** Use an intuitive **noun** in PascalCase (e.g. `Library`,
  `Calendar`, `BlobStore`). Avoid names that clash with common language/runtime
  concepts (e.g. `File`). If needed, add a suffix like `Api` or `Service` to
  disambiguate.
- **Methods:** Prefer **standard methods** (Get, List, Create, Update, Delete)
  over custom methods. Group RPCs by resource; list standard methods before
  custom ones.

## Resource-oriented design

- Model the API as a **resource hierarchy**: resources (nouns) and collections;
  use a small set of **standard methods** plus **custom methods** when
  necessary.
- Each resource **must** support **Get**. All
  non-[singleton](https://google.aip.dev/156) resources **must** support
  **List**.
- Resource schema (message shape) for a given resource **must** be the same
  across all methods that take or return that resource.
- Relationships must form a **directed acyclic graph**; each resource has **at
  most one canonical parent**. Use `parent` for collection scope and optional
  `filter` for other associations (AIP-124, AIP-160).

## Resource names

- **Format:** Path-like, without leading slash:
  `publishers/123/books/les-miserables`. Use `/` only as segment separator;
  **no `/` inside** a segment.
- **Segments:** Alternate **collection identifiers** (plural, camelCase, e.g.
  `publishers`, `books`) and **resource ID** segments. Collection IDs must be
  unique within a single resource name (no `people/xyz/people/abc`).
- **Characters:** Prefer DNS-safe (RFC 1123); avoid uppercase in IDs; avoid
  URL-encoding; if Unicode is needed, use NFC (AIP-210).
- **User-specified IDs:** Document format; prefer lowercase letters, numbers,
  hyphen; first character letter, last letter or number; max 63 chars (RFC 1034
  style). Duplicate name → `ALREADY_EXISTS` (or `PERMISSION_DENIED` if user
  cannot see the duplicate).
- **Full resource name** (cross-API): schemeless URI with service name +
  relative name, e.g.
  `//library.googleapis.com/publishers/123/books/les-miserables`.

## Resource types and annotations

- **Resource type:** `{ServiceName}/{Type}` (e.g.
  `library.googleapis.com/Book`). Type must match the message name, singular,
  PascalCase, alphanumeric.
- **Annotation:** Use `google.api.resource` with `type`, `pattern`, `singular`,
  `plural`. Pattern variables: **snake_case**, no `_id` suffix, unique within
  pattern. Pattern variables match singular resource type (e.g. `{topic}` for
  Topic).
- **Nested collections:** Child collection segment may drop redundant prefix
  (e.g. `users/{user}/events/{event}` instead of `userEvents` in path);
  message/type name stays e.g. `UserEvent`; `singular`/`plural` not shortened.

## Fields for resource names

- **On the resource message:** First field **should** be `string name` with
  resource name; annotate with `(google.api.field_behavior) = IDENTIFIER` and
  `google.api.resource`.
- **In request messages (acting on one resource):** Use `string name` for the
  resource; annotate with `REQUIRED` and `google.api.resource_reference`
  (`type` or `child_type`). Comment **should** document the pattern (e.g.
  `Format: publishers/{publisher}/books/{book}`).
- **In request messages (collection scope):** Use `string parent` for the
  collection's parent resource; same annotations and pattern comment.
- **Referencing another resource:** Prefer `string` with resource name; field
  name ≈ referenced type in snake_case (e.g. `shelf`); use
  `google.api.resource_reference`. Do **not** embed the other resource's
  message type (except internal/revisions cases in AIP-162). Use `_name` suffix
  only if needed to avoid ambiguity (e.g. `crypto_key_name`).
- **Reserved:** Use `name` only for resource name; use `parent` only for parent
  collection. For other concepts use a different name or adjective (e.g.
  `display_name`).
