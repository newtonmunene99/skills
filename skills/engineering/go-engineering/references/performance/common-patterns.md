# Common Go Patterns for Performance (Part 1)

Condensed reference for memory, concurrency, I/O, and compiler optimizations. Based on the [Go Optimization Guide](https://goperf.dev).

## Table of contents

- [Memory Management & Efficiency](#memory-management--efficiency) — pooling, prealloc, alignment, interface boxing, zero-copy, GC, stack vs heap
- [Concurrency and Synchronization](#concurrency-and-synchronization) — worker pools, atomics, lazy init, immutable data, context
- [I/O Optimization and Throughput](#io-optimization-and-throughput) — buffered I/O, batching
- [Compiler-Level Optimization and Tuning](#compiler-level-optimization-and-tuning) — compiler flags, escape analysis

---

## Memory Management & Efficiency

| Topic | Recommendations |
|-------|-----------------|
| **Object pooling** | Use `sync.Pool` for short-lived or frequently reused structs (e.g. byte buffers, request-scoped objects). Get/Put on hot paths; not a silver bullet—measure first. |
| **Memory preallocation** | Preallocate slices and maps: `make([]T, 0, expectedSize)`, `make(map[K]V, n)` to avoid resizes and copying. |
| **Struct field alignment** | Order fields by decreasing alignment (largest first) to minimize padding; use padding to avoid false sharing (e.g. 64-byte cache-line separation) in concurrent structs. |
| **Interface boxing** | Assigning concrete values to interfaces can allocate (heap copy). Avoid slices of interfaces or interface params on hot paths; use concrete types or pointers where possible. |
| **Zero-copy** | Use slicing and buffer reuse to avoid copying; sub-slices and in-place updates where safe. |
| **GC** | Minimize heap usage and reuse memory. Tune GOGC/GOMEMLIMIT only after profiling; default is usually best. Use GOMEMLIMIT in containers to avoid OOM. |
| **Stack vs heap** | Use escape analysis: `go build -gcflags="-m" ./pkg`. Avoid returning pointers to locals, capturing locals in closures, or storing in package-level vars if you want stack allocation. |

### Examples (from [goperf.dev](https://goperf.dev))

**Object pooling** — avoid allocating on every use:

```go
// Bad: new allocation every iteration
func createData() *Data { return &Data{Value: 42} }
for i := 0; i < 1000000; i++ {
    obj := createData()
    _ = obj
}

// Good: retrieve from pool, use, return
var dataPool = sync.Pool{
    New: func() any { return &Data{} },
}
for i := 0; i < 1000000; i++ {
    obj := dataPool.Get().(*Data)
    obj.Value = 42
    dataPool.Put(obj)
}
```

Pooling byte buffers (e.g. for I/O):

```go
var bufferPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}
buf := bufferPool.Get().(*bytes.Buffer)
buf.Reset()
buf.WriteString("Hello, pooled world!")
bufferPool.Put(buf)
```

**Memory preallocation** — avoid repeated slice/map growth:

```go
// Bad: slice grows repeatedly
var result []int
for i := 0; i < 10000; i++ {
    result = append(result, i)
}

// Good: preallocate capacity
result := make([]int, 0, 10000)
for i := 0; i < 10000; i++ {
    result = append(result, i)
}
```

Maps: use `make(map[K]V, n)` when size is known:

```go
// Bad
m := make(map[int]string)
for i := 0; i < 10000; i++ { m[i] = fmt.Sprintf("val-%d", i) }

// Good
m := make(map[int]string, 10000)
for i := 0; i < 10000; i++ { m[i] = fmt.Sprintf("val-%d", i) }
```

**Struct field alignment** — minimize padding; avoid false sharing:

```go
// Bad: PoorlyAligned — 24 bytes on 64-bit (padding between fields)
type PoorlyAligned struct {
    flag  bool
    count int64
    id    byte
}

// Good: WellAligned — 16 bytes (largest alignment first)
type WellAligned struct {
    count int64
    flag  bool
    id    byte
}
```

Concurrent counters: pad to avoid false sharing (same cache line):

```go
// Bad: a and b can share a cache line; concurrent updates cause invalidations
type SharedCounterBad struct {
    a int64
    b int64
}

// Good: padding so a and b live on different 64-byte cache lines
type SharedCounterGood struct {
    a int64
    _ [56]byte
    b int64
}
```

**Interface boxing** — avoid hidden allocations:

```go
type Shape interface { Area() float64 }
type Square struct { Size float64 }
func (s Square) Area() float64 { return s.Size * s.Size }

// Bad: each Square is copied onto heap when appended to []Shape
var shapes []Shape
for i := 0; i < 1000; i++ {
    s := Square{Size: float64(i)}
    shapes = append(shapes, s)
}

// Good: pass pointer — only 8-byte pointer stored in interface
    shapes = append(shapes, &s)
```

**Stack vs heap** — avoid unnecessary escapes:

```go
// Bad: x escapes to heap because pointer is returned
func allocate() *int {
    x := 42
    return &x
}

// Good: return value so it can stay on stack
func noEscape() int {
    x := 42
    return x
}
```

Other escape causes: capturing locals in closures, storing in package-level vars, assigning to interface. Use `go build -gcflags="-m" ./pkg` to see what escapes.

---

## Concurrency and Synchronization

| Topic | Recommendations |
|-------|-----------------|
| **Worker pools** | Fixed-size goroutine pool + job channel for backpressure and predictable resource use. |
| **Atomics** | Use `sync/atomic` or lightweight locks for shared counters/state; avoid coarse locks on hot paths. |
| **Lazy init** | `sync.Once` for one-time expensive setup. |
| **Immutable data** | Share read-only data across goroutines to avoid locks. |
| **Context** | Propagate timeouts and cancellation with `context.Context`; set deadlines on requests and I/O. |

### Examples (from [goperf.dev](https://goperf.dev))

**Worker pool** — fixed pool of workers + job channel:

```go
func worker(id int, jobs <-chan int, results chan<- [32]byte) {
    for j := range jobs {
        results <- doWork(j)
    }
}

jobs := make(chan int, 100)
results := make(chan [32]byte, 100)
for w := 1; w <= 5; w++ {
    go worker(w, jobs, results)
}
for j := 1; j <= 10; j++ { jobs <- j }
close(jobs)
for a := 1; a <= 10; a++ { <-results }
```

**Lazy init** — defer expensive setup until first use:

```go
// sync.Once: expensiveInit() runs exactly once, even with concurrent getResource() calls
var (
    resource *MyResource
    once     sync.Once
)
func getResource() *MyResource {
    once.Do(func() {
        resource = expensiveInit()
    })
    return resource
}
```

Go 1.21+: `sync.OnceValue` for initialization that returns a value:

```go
var getResource = sync.OnceValue(func() *MyResource {
    return expensiveInit()
})
```

---

## I/O Optimization and Throughput

| Topic | Recommendations |
|-------|-----------------|
| **Buffered I/O** | Use `bufio.Reader` / `bufio.Writer` to reduce system calls. |
| **Batching** | Batch small operations to reduce round trips and amortize overhead. |

### Examples (from [goperf.dev](https://goperf.dev))

**Buffered I/O** — reduce system calls:

```go
// Bad: 10,000 separate writes = 10,000 syscalls
f, _ := os.Create("output.txt")
for i := 0; i < 10000; i++ {
    f.Write([]byte("line\n"))
}

// Good: bufio.Writer batches writes; flush when buffer full or done
f, _ := os.Create("output.txt")
buf := bufio.NewWriter(f)
for i := 0; i < 10000; i++ {
    buf.WriteString("line\n")
}
buf.Flush()
```

Always call `Flush()` before closing; unwritten buffer data is lost otherwise. For larger throughput, use `bufio.NewWriterSize(f, 16*1024)` or `bufio.NewReaderSize(f, 32*1024)` and measure.

---

## Compiler-Level Optimization and Tuning

| Topic | Recommendations |
|-------|-----------------|
| **Compiler flags** | `-ldflags="-s -w"` for smaller binaries; `-gcflags="all=-N -l"` to disable optimizations/inlining for debugging. Use build tags and GOOS/GOARCH for cross-builds. |
| **Escape analysis** | `go build -gcflags="-m" ./pkg` to see what escapes to the heap; refactor hot paths to keep values on the stack. |
