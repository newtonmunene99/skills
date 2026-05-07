# Naming summary and standard methods

Read this when checking naming conventions or RPC/method patterns for standard methods.

## Standard methods

| Method | RPC name                      | Request suffix | Response                                                 | HTTP   | Body     |
| ------ | ----------------------------- | -------------- | -------------------------------------------------------- | ------ | -------- |
| Get    | `Get{Resource}` (singular)    | `Request`      | Resource                                                 | GET    | none     |
| List   | `List{Resources}` (plural)    | `Request`      | `List{Resources}Response`                                | GET    | none     |
| Create | `Create{Resource}` (singular) | `Request`      | Resource (or LRO)                                        | POST   | resource |
| Update | `Update{Resource}` (singular) | `Request`      | Resource (or LRO)                                        | PATCH  | resource |
| Delete | `Delete{Resource}` (singular) | `Request`      | `google.protobuf.Empty` or resource (soft delete) or LRO | DELETE | none     |

## Naming summary

| Element             | Convention           | Example                       |
| ------------------- | -------------------- | ----------------------------- |
| Package             | lowercase, versioned | `google.library.v1`           |
| File                | snake_case           | `library_service.proto`       |
| Service (interface) | Noun, PascalCase     | `Library`                     |
| Resource type       | {ServiceName}/{Type} | `library.googleapis.com/Book` |
| Resource message    | Singular, PascalCase | `Book`                        |
| Collection (path)   | Plural, camelCase    | `publishers`, `books`         |
| Pattern variable    | snake_case, singular | `{publisher}`, `{book}`       |
| RPC (standard)      | Verb + Noun          | `GetBook`, `ListBooks`        |
| RPC (custom)        | Verb + Noun          | `ArchiveBook`                 |
| Request message     | RPC + Request        | `GetBookRequest`              |
| List response       | List + Response      | `ListBooksResponse`           |
| Field               | lower_snake_case     | `create_time`, `page_size`    |
| Enum value          | UPPER_SNAKE_CASE     | `FORMAT_UNSPECIFIED`          |
