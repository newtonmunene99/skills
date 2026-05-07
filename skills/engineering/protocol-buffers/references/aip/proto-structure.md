# Proto File Structure and Packages

Read this when setting up a new `.proto` file, organizing imports, or deciding where to place API-specific vs common protos.

## Package and file structure

- **Package:** Each API **must** live in a single package that **ends in a
  major version** (e.g. `google.library.v1`). Directory layout **must** match
  the package (e.g. `google/library/v1`).
- **Syntax:** Use `proto3` only.
- **File names:** Use `snake_case`. APIs **should** have an obvious "entry"
  file, generally named after the API itself. Service definitions and associated
  RPC request/response messages **should** be in the same file. Avoid language
  keywords (e.g. not `import.proto`). **Must not** use the version as the
  filename (e.g. no `v1.proto`).
- **File layout order:** Syntax → package → imports (alphabetical) → file
  options → services (standard methods before custom, grouped by resource) →
  resource messages (parent before child) → request/response messages (matching
  RPC order, request before response) → other messages → top-level enums.
  Optionally prepend a copyright/license notice if other protos in the project
  use one or it is explicitly requested.

## Packaging annotations (AIP-191)

Language-specific package/namespace annotations override the inferred defaults.
Only set annotations for languages the project actually targets or generates
stubs for. Infer which languages are relevant from the project structure,
build config, or existing protos.

- **Java** (only if generating Java stubs):
  - `java_package` — set to the proto package with TLD prefix (e.g.
    `com.google.example.v1`).
  - `java_multiple_files` — set to `true`.
  - `java_outer_classname` — set to the filename in PascalCase + `Proto`
    (e.g. `LibraryProto`).
- **C#/Ruby/PHP** — only needed if generating stubs for these languages. If
  any part of the package is a compound name, these options **must** be
  specified to account for word breaks using PascalCase (e.g.
  `option csharp_namespace = "Google.Cloud.AccessApproval.V1";`).
- **Go** — `go_package` depends on how the Go code is managed. The terminal
  import path segment **should** be suffixed with `pb` (e.g.
  `accessapprovalpb`). Version segments **should** be prefixed with `api`
  (e.g. `v1` becomes `apiv1`).
- All packaging annotations **should** be in alphabetical order by name.
- Adding a packaging annotation (with a value not equivalent to the default)
  is a **breaking change** in that language.

## API-specific vs common protos

- **API-specific protos** belong in the versioned package (e.g.
  `google.library.v1`). Do **not** create shared "API-specific common" packages
  across versions; duplicate the proto per version if needed (AIP-215).
- **Cross-API references:** Use **resource names** (strings), not the resource
  message type from another API.
- **Common components (AIP-213):** APIs **may** import:
  - `google.api.*` (not subpackages)
  - `google.longrunning.Operation`
  - `google.protobuf.*` (e.g. `Timestamp`, `Duration`, `Struct`, `FieldMask`,
    `Empty`)
  - `google.rpc.*`
  - `google.type.*` (e.g. `Date`, `Money`, `LatLng`, `PostalAddress`,
    `TimeOfDay`)
  - `google.iam.v1.*` where relevant
- **Organization-specific common packages** must end with `.type` (e.g.
  `google.geo.type`), be published in the googleapis repo, and follow AIP-213;
  do **not** put generic types there.
