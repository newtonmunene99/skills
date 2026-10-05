---
name: protocol-buffers
description: >-
  Best practices for designing and working with protocol buffers and
  resource-oriented APIs. Covers proto file structure, services, resource
  naming, standard and custom RPC methods, message and field conventions,
  field numbering, breaking changes, and AIP guidelines from google.aip.dev,
  validated with the API Linter. Use whenever a .proto file, gRPC service or
  REST resource API is created, extended or reviewed — including adding a
  field, enum value or RPC to an existing message, asking "is this a breaking
  change", designing a gRPC service for something, or fixing api-linter or
  buf lint output — even if AIP is not mentioned. Comment wording on protos
  belongs to code-documentation; reviewing a whole diff or PR belongs to
  git-code-review, with this skill supplying the proto checks.
disable-model-invocation: false
compatibility: >-
  The API Linter (github.com/googleapis/api-linter) is the validation step.
  When it is not installed, the skill gives the install command instead of
  treating a compile as validation.
---

# Protocol Buffers & API Design

## Overview

Best practices for designing protocol buffers, RPCs, services, messages, fields,
and naming for APIs that follow [resource-oriented design](https://google.aip.dev/121).
Currently covers general AIP guidance from [google.aip.dev](https://google.aip.dev/)
(AIPs in approved state). Domain-specific AIPs (Cloud, Firebase, Auth, etc.) may
add further rules.

## Workflow

1. **Identify what you're designing or reviewing** — new service, resource hierarchy, RPC shape, field naming, proto file structure, or an **addition to an existing message or service** (the most common case; see [Adding to an existing contract](references/aip/messages-and-fields.md#adding-to-an-existing-contract)).
2. **Read the matching reference before writing or approving anything** — use the routing table below. The Quick Cues are a reminder, not a substitute: rules such as no prepositions in field names and when to use `optional` live only in the references.
3. **Follow AIP, and flag where the repo differs.** When the surrounding protos break an AIP rule (no `field_behavior`, `expiry_time` instead of `expire_time`, `Delete` returning the resource on a hard delete), write the new code to AIP anyway. In your reply, list each place the new code now differs from the repo's convention, one line each, and ask whether the user wants it to follow the repo instead. Never copy a repo pattern that is wrong for the new resource, such as `show_deleted` on a resource without soft delete, because it promises behavior the server does not have and becomes a breaking change to remove.
4. **Validate with the API Linter, not just the compiler.** `buf build` or `protoc` only proves the file compiles. Run `api-linter --set-exit-status -I <proto_root> <changed>.proto` (add `-I` for each import root). In a repo with existing violations, report only findings on lines you changed. Fix them, or document a deliberate exception with `aip.dev/not-precedent`. If the linter is not installed, say so and give the install command (`go install github.com/googleapis/api-linter/cmd/api-linter@latest`) rather than presenting a compile as validation.

## When to Read Which Reference

### AIP Guidelines (google.aip.dev)

- **Proto file structure, packages, imports, layout** → Read [references/aip/proto-structure.md](references/aip/proto-structure.md)
- **Services, resource hierarchy, resource names, types, annotations** → Read [references/aip/resources-and-services.md](references/aip/resources-and-services.md)
- **RPCs, HTTP transcoding, standard methods, custom methods, LRO** → Read [references/aip/rpcs-and-methods.md](references/aip/rpcs-and-methods.md)
- **Messages, field naming, field behavior, standard fields, pagination, errors** → Read [references/aip/messages-and-fields.md](references/aip/messages-and-fields.md)
- **Full minimal CRUD example (service, resource, request/response messages)** → Read [references/aip/full-example.md](references/aip/full-example.md)
- **Naming conventions table, standard methods table** → Read [references/aip/naming-and-methods.md](references/aip/naming-and-methods.md)

## Neighbours

- **code-documentation** owns comment and doc wording, including `.proto` comments; this skill owns the API shape and says where a comment is required.
- **git-code-review** owns reviewing a diff, commit, branch or PR and writes the report; this skill supplies the proto and AIP checks for it.

## Quick Cues

- **File layout:** Syntax → package → imports (alphabetical) → options → services → resource messages → request/response messages → enums. Add copyright/license header only if other protos in the project use one.
- **Resource names:** Path-like without leading slash (`publishers/123/books/abc`); alternate collection (plural, camelCase) and ID segments.
- **Standard methods first:** Get, List, Create, Update, Delete before custom methods. Prefer standard methods whenever possible.
- **Field naming:** `lower_snake_case`; no `is_` prefix on booleans; use `_time` suffix for timestamps; `_count` not `num_`; no prepositions (`error_reason`, not `reason_for_error`; `caller_owned`, not `owned_by_caller`); nouns, not verbs; repeated fields plural.
- **`optional` only when zero ≠ unset (AIP-149):** for a primitive where the zero value is meaningful (`optional int32 max_retries`). Not for IDs, names or strings where empty already means "not provided".
- **Adding a field:** next unused number, skipping `reserved` ranges; never reuse or renumber. Adding is non-breaking; renaming, retyping or renumbering is breaking. Say which in your summary.
- **Field behavior on every request field:** `REQUIRED`, `OPTIONAL`, `OUTPUT_ONLY` or `IDENTIFIER` (resource `name` only). api-linter's `core::0203::field-behavior-required` flags any request field without one, including the fields of a resource sent in a Create or Update.
- **Pagination from day one:** List must have `page_size`, `page_token`, `next_page_token`.
- **Document everything:** Leading comments on every service, method, message, field, enum; api-linter's `core::0192::has-comments` flags any that lack one. Never trailing or inline: client-library doc generators read only leading comments, and `core::0192::only-leading-comments` flags the rest. For comment wording and style, use code-documentation.
- **Backwards compatibility:** No breaking changes within a major version. Adding a packaging annotation is a breaking change.

## References

- **AIP index:** [google.aip.dev](https://google.aip.dev/)
- **API Linter:** [github.com/googleapis/api-linter](https://github.com/googleapis/api-linter)
- **Key AIPs:** 1 (purpose), 8 (style), 121 (resource design), 122 (resource
  names), 123 (resource types), 126 (enums), 127 (HTTP transcoding), 131-136
  (standard + custom methods), 140 (field names), 141 (quantities), 142
  (time/duration), 148 (standard fields), 149 (unset field values), 154
  (etag), 155 (request ID), 158 (pagination), 164 (soft delete), 190
  (naming), 191 (file structure), 192 (documentation), 193 (errors), 200
  (precedent), 202 (field info/formats), 203 (field behavior), 213 (common
  components), 215 (API-specific protos), 216 (states)
