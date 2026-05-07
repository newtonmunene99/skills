# Full minimal CRUD example

Read this when implementing a new service or checking request/response shape for standard methods.

```proto
syntax = "proto3";
package google.example.library.v1;

import "google/api/field_behavior.proto";
import "google/api/resource.proto";
import "google/api/annotations.proto";
import "google/protobuf/field_mask.proto";
import "google/protobuf/timestamp.proto";

service Library {
  rpc GetBook(GetBookRequest) returns (Book) {
    option (google.api.http) = { get: "/v1/{name=publishers/*/books/*}" };
    option (google.api.method_signature) = "name";
  }
  rpc ListBooks(ListBooksRequest) returns (ListBooksResponse) {
    option (google.api.http) = { get: "/v1/{parent=publishers/*}/books" };
    option (google.api.method_signature) = "parent";
  }
  rpc CreateBook(CreateBookRequest) returns (Book) {
    option (google.api.http) = {
      post: "/v1/{parent=publishers/*}/books"
      body: "book"
    };
    option (google.api.method_signature) = "parent,book,book_id";
  }
  rpc UpdateBook(UpdateBookRequest) returns (Book) {
    option (google.api.http) = {
      patch: "/v1/{book.name=publishers/*/books/*}"
      body: "book"
    };
    option (google.api.method_signature) = "book,update_mask";
  }
  rpc DeleteBook(DeleteBookRequest) returns (google.protobuf.Empty) {
    option (google.api.http) = { delete: "/v1/{name=publishers/*/books/*}" };
    option (google.api.method_signature) = "name";
  }
}

message Book {
  option (google.api.resource) = {
    type: "library.googleapis.com/Book"
    pattern: "publishers/{publisher}/books/{book}"
    singular: "book"
    plural: "books"
  };
  string name = 1 [(google.api.field_behavior) = IDENTIFIER];
  string display_name = 2;
  google.protobuf.Timestamp create_time = 3 [(google.api.field_behavior) = OUTPUT_ONLY];
  google.protobuf.Timestamp update_time = 4 [(google.api.field_behavior) = OUTPUT_ONLY];
}

message GetBookRequest {
  string name = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = { type: "library.googleapis.com/Book" }
  ];
}

message ListBooksRequest {
  string parent = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = { child_type: "library.googleapis.com/Book" }
  ];
  int32 page_size = 2;
  string page_token = 3;
}

message ListBooksResponse {
  repeated Book books = 1;
  string next_page_token = 2;
}

message CreateBookRequest {
  string parent = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = { child_type: "library.googleapis.com/Book" }
  ];
  string book_id = 2 [(google.api.field_behavior) = REQUIRED];
  Book book = 3 [(google.api.field_behavior) = REQUIRED];
}

message UpdateBookRequest {
  Book book = 1 [(google.api.field_behavior) = REQUIRED];
  google.protobuf.FieldMask update_mask = 2;
}

message DeleteBookRequest {
  string name = 1 [
    (google.api.field_behavior) = REQUIRED,
    (google.api.resource_reference) = { type: "library.googleapis.com/Book" }
  ];
}
```
