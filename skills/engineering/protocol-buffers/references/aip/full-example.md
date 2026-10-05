# Full minimal CRUD example

Read this when implementing a new service or checking request/response shape for standard methods. It compiles and passes `api-linter` with no findings, so treat each import, annotation and comment as part of the shape, not decoration. The `java_*` options are there only because api-linter's `core::0191` rules check them on every file; a project that does not generate Java can disable those three rules instead (see [proto-structure.md](proto-structure.md#packaging-annotations-aip-191)).

```proto
syntax = "proto3";

package google.example.library.v1;

import "google/api/annotations.proto";
import "google/api/client.proto";
import "google/api/field_behavior.proto";
import "google/api/resource.proto";
import "google/protobuf/empty.proto";
import "google/protobuf/field_mask.proto";
import "google/protobuf/timestamp.proto";

option java_multiple_files = true;
option java_outer_classname = "LibraryProto";
option java_package = "com.google.example.library.v1";

// Manages books in a library.
service Library {
  // Gets a book.
  rpc GetBook(GetBookRequest) returns (Book) {
    option (google.api.http) = {
      get: "/v1/{name=publishers/*/books/*}"
    };
    option (google.api.method_signature) = "name";
  }

  // Lists the books of a publisher.
  rpc ListBooks(ListBooksRequest) returns (ListBooksResponse) {
    option (google.api.http) = {
      get: "/v1/{parent=publishers/*}/books"
    };
    option (google.api.method_signature) = "parent";
  }

  // Creates a book under a publisher.
  rpc CreateBook(CreateBookRequest) returns (Book) {
    option (google.api.http) = {
      post: "/v1/{parent=publishers/*}/books"
      body: "book"
    };
    option (google.api.method_signature) = "parent,book,book_id";
  }

  // Updates a book.
  rpc UpdateBook(UpdateBookRequest) returns (Book) {
    option (google.api.http) = {
      patch: "/v1/{book.name=publishers/*/books/*}"
      body: "book"
    };
    option (google.api.method_signature) = "book,update_mask";
  }

  // Deletes a book permanently.
  rpc DeleteBook(DeleteBookRequest) returns (google.protobuf.Empty) {
    option (google.api.http) = {
      delete: "/v1/{name=publishers/*/books/*}"
    };
    option (google.api.method_signature) = "name";
  }
}

// A book in a publisher's catalog.
message Book {
  option (google.api.resource) = {
    type: "library.googleapis.com/Book"
    pattern: "publishers/{publisher}/books/{book}"
    singular: "book"
    plural: "books"
  };

  // The resource name of the book.
  // Format: publishers/{publisher}/books/{book}
  string name = 1 [(google.api.field_behavior) = IDENTIFIER];

  // The human-readable title shown to readers.
  string display_name = 2 [(google.api.field_behavior) = OPTIONAL];

  // When the book was created.
  google.protobuf.Timestamp create_time = 3
      [(google.api.field_behavior) = OUTPUT_ONLY];

  // When the book was last updated.
  google.protobuf.Timestamp update_time = 4
      [(google.api.field_behavior) = OUTPUT_ONLY];
}

// Request message for `GetBook`.
message GetBookRequest {
  // The name of the book to get.
  // Format: publishers/{publisher}/books/{book}
  string name = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = { type: "library.googleapis.com/Book" }
  ];
}

// Request message for `ListBooks`.
message ListBooksRequest {
  // The publisher that owns the books.
  // Format: publishers/{publisher}
  string parent = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = {
      child_type: "library.googleapis.com/Book"
    }
  ];

  // The maximum number of books to return. The server returns at most 1000
  // and uses 50 when this is unset or zero.
  int32 page_size = 2 [(google.api.field_behavior) = OPTIONAL];

  // A page token from a previous `ListBooks` call, used to get the next page.
  string page_token = 3 [(google.api.field_behavior) = OPTIONAL];
}

// Response message for `ListBooks`.
message ListBooksResponse {
  // The books of the publisher.
  repeated Book books = 1;

  // A token to get the next page, or empty when there are no more pages.
  string next_page_token = 2;
}

// Request message for `CreateBook`.
message CreateBookRequest {
  // The publisher to create the book under.
  // Format: publishers/{publisher}
  string parent = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = {
      child_type: "library.googleapis.com/Book"
    }
  ];

  // The ID to use for the book, which becomes the final segment of its name.
  string book_id = 2 [(google.api.field_behavior) = REQUIRED];

  // The book to create.
  Book book = 3 [(google.api.field_behavior) = REQUIRED];
}

// Request message for `UpdateBook`.
message UpdateBookRequest {
  // The book to update. Its `name` identifies which book.
  Book book = 1 [(google.api.field_behavior) = REQUIRED];

  // The fields to update. When unset, every populated field is updated.
  google.protobuf.FieldMask update_mask = 2
      [(google.api.field_behavior) = OPTIONAL];
}

// Request message for `DeleteBook`.
message DeleteBookRequest {
  // The name of the book to delete.
  // Format: publishers/{publisher}/books/{book}
  string name = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = { type: "library.googleapis.com/Book" }
  ];
}
```
