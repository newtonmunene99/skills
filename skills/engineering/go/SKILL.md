---
name: go-engineering
description: >-
  Best practices for writing performant, idiomatic, and readable Go code.
  Covers performance optimization (memory, allocations, GC, networking,
  concurrency) from goperf.dev and code style (naming, formatting,
  readability, simplicity) from the Google Go Style Guide. Use when
  writing, reviewing, or optimizing Go code, or when asking about Go
  naming conventions, performance patterns, style, or readability.
disable-model-invocation: false
---

# Go Engineering

## Overview

Apply measurement-driven performance patterns from the [Go Optimization Guide](https://goperf.dev) and idiomatic style and readability principles from the [Google Go Style Guide](https://google.github.io/styleguide/go). Measure first (benchmarks, pprof, escape analysis); then apply targeted patterns. Focus on production workloads: backend services, pipelines, and systems where latency, throughput, and long-term maintainability matter.

## Workflow

1. **Establish a baseline** — Add or run benchmarks; profile under load with pprof (CPU, memory). Optimizing without numbers often targets the wrong place; a baseline makes the impact of changes observable and avoids wasted effort.
2. **Identify the bottleneck** — Allocations/GC, I/O, scheduler, or networking. Use `go build -gcflags="-m" ./pkg` to see what escapes to the heap.
3. **Apply patterns from references** — Use the appropriate reference file below; all recommendations are self-contained in this skill. Each reference is organized by section with tables and code examples; jump to the section that matches the bottleneck. For extended articles, see [goperf.dev](https://goperf.dev).

## When to Read Which Reference

### Performance (goperf.dev)

- **Memory, allocations, GC, concurrency, I/O, compiler flags, escape analysis** → Read [references/performance/common-patterns.md](references/performance/common-patterns.md) (see its table of contents to find the right section).
- **HTTP, Transport tuning, connection reuse, 10k+ connections, TLS, DNS, load shedding, backpressure, TCP/HTTP/2/gRPC/QUIC** → Read [references/performance/networking.md](references/performance/networking.md) (see its table of contents to find the right section).

### Style Guide (Google Go Style Guide)

- **Code style, naming, formatting, readability, simplicity, and idiomatic Go practices** → Read [references/styleguide/guide.md](references/styleguide/guide.md) for core principles, [references/styleguide/best-practices.md](references/styleguide/best-practices.md) for idioms, and [references/styleguide/decisions.md](references/styleguide/decisions.md) for rationale.

## Quick Cues

- **Connection reuse (HTTP)**: Drain response body before closing (e.g. `io.Copy(io.Discard, resp.Body)` then `resp.Body.Close()`); otherwise the client will not reuse connections.
- **Escape analysis**: Run `go build -gcflags="-m" ./path/to/pkg` to see which values move to the heap; reduce escapes on hot paths to lower GC pressure.
- **Code Style (Naming & MixedCaps)**: Use `MixedCaps` or `mixedCaps` (camel case) rather than underscores (snake case) for multi-word names. Keep names short and contextual without repetition.

## Edge cases and examples

- **Optimizing without data**: Avoid suggesting pooling, prealloc, or GOGC changes until the user has (or is guided to) benchmarks or pprof evidence—suggestions without data often target the wrong bottleneck and add complexity without benefit. Recommend measuring first.
- **Networking**: When suggesting Transport or connection changes, remind to drain response bodies for connection reuse and to tune timeouts and limits to match the workload; otherwise connections may not be reused or may be held too long.
