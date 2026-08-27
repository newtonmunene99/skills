# Practical Networking Patterns in Go (Part 2)

Condensed reference for high-performance networking in Go. Based on the [Go Optimization Guide](https://goperf.dev).

## Table of contents

- [Benchmarking First](#benchmarking-first) — establish baselines before optimizing
- [Foundations and Core Concepts](#foundations-and-core-concepts) — connection reuse, Transport tuning, pooling, observability
- [Scaling and Performance Engineering](#scaling-and-performance-engineering) — 10k+ connections, GOMAXPROCS
- [Diagnostics and Resilience](#diagnostics-and-resilience) — load shedding, long-lived connections, buffer leaks
- [Transport-Level Optimization](#transport-level-optimization) — TCP/HTTP/2/gRPC, QUIC
- [Low-Level and Advanced Tuning](#low-level-and-advanced-tuning) — socket options, DNS, TLS, fresh DNS

---

## Benchmarking First

- **Establish baselines before optimizing.** Use vegeta, wrk, or k6 for throughput, latency percentiles, and connection concurrency; profile under load.

---

## Foundations and Core Concepts

| Topic | Recommendations |
|-------|-----------------|
| **Networking internals** | Understand goroutines, the `net` package, scheduler, blocking I/O, and pollers (epoll/kqueue). |
| **Efficient net/http and net.Conn** | Drain response body before close (`io.Copy(io.Discard, resp.Body)` then `resp.Body.Close()`) so connections are reused. Tune `http.Transport`: MaxIdleConns, MaxIdleConnsPerHost, MaxConnsPerHost, IdleConnTimeout, ExpectContinueTimeout; use a custom Dialer (Timeout, KeepAlive). Avoid leaking connections and blocking handlers. |

### Examples (from [goperf.dev](https://goperf.dev))

**Connection reuse** — drain body before close; otherwise the client opens new TCP connections every time:

```go
// Bad: body not drained — connections are not reused under load
resp, err := client.Get("http://localhost:8080/data")
if err != nil { log.Fatal(err) }
defer resp.Body.Close()

// Good: drain then close so connection returns to pool
io.Copy(io.Discard, resp.Body)
resp.Body.Close()
```

**Tuned http.Transport** — match your concurrency and timeouts:

```go
transport := &http.Transport{
    MaxIdleConns:          1000,
    MaxConnsPerHost:       100,
    IdleConnTimeout:       90 * time.Second,
    ExpectContinueTimeout: 0,
    DialContext: (&net.Dialer{
        Timeout:   5 * time.Second,
        KeepAlive: 30 * time.Second,
    }).DialContext,
}
client := &http.Client{
    Transport: transport,
    Timeout:   2 * time.Second,
}
```

Use a dedicated `http.Client` per upstream host to avoid mixing connection pools and head-of-line blocking. Set `ExpectContinueTimeout: 0` if you don't need 100-continue. Prefer a tight `Client.Timeout` (e.g. 2s) and retries with backoff instead of very long timeouts.

**Pooling bufio.Reader/Writer** — reduce allocation churn for many connections:

```go
var readerPool = sync.Pool{
    New: func() any { return bufio.NewReaderSize(nil, 4096) },
}
func getReader(conn net.Conn) *bufio.Reader {
    r := readerPool.Get().(*bufio.Reader)
    r.Reset(conn)
    return r
}
```

**Connection observability** — log state transitions to debug leaks or stuck connections:

```go
server := &http.Server{
    ConnState: func(conn net.Conn, state http.ConnState) {
        log.Printf("conn %v → %v", conn.RemoteAddr(), state)
    },
}
```

---

## Scaling and Performance Engineering

| Topic | Recommendations |
|-------|-----------------|
| **10k+ connections** | Resource capping, socket tuning, runtime config, connection lifecycles. |
| **GOMAXPROCS and scheduler** | GOMAXPROCS, GODEBUG, thread pinning, epoll/kqueue interaction; understand when more parallelism helps vs doesn’t. |

---

## Diagnostics and Resilience

| Topic | Recommendations |
|-------|-----------------|
| **Load shedding and backpressure** | Circuit breakers, passive/active load shedding, channel buffering and timeouts, graceful degradation. |
| **Long-lived connections** | Avoid leaks: set read/write deadlines, manage backpressure, use heap profiling to trace growth (WebSockets, TCP streams). |

### Examples (from [goperf.dev](https://goperf.dev))

**Long-lived connections: buffer slice leak** — passing a slice that shares a backing array retains the whole buffer:

```go
// Bad: data points at the 4KB pool buffer; if process stores it, the whole buffer is retained
data := buf[:n]
go process(data)

// Good: copy into a new slice so the pool buffer can be reused
data := make([]byte, n)
copy(data, buf[:n])
go process(data)
```

Set read/write deadlines on connections so blocked reads don't leave goroutines and buffers alive forever. Use heap profiling to trace growth under sustained load.

---

## Transport-Level Optimization

| Topic | Recommendations |
|-------|-----------------|
| **TCP, HTTP/2, gRPC** | Weigh trade-offs: latency, throughput, connection reuse, CPU/memory. |
| **QUIC** | quic-go for low-latency, multiplexed streams; connection migration, 0-RTT. |

---

## Low-Level and Advanced Tuning

| Topic | Recommendations |
|-------|-----------------|
| **Socket options** | TCP_NODELAY, SO_REUSEPORT, SO_RCVBUF/SO_SNDBUF, keepalives, SOMAXCONN; use via syscall where needed. |
| **DNS** | Resolver (cgo vs Go), caching, custom dialers, pre-resolved IPs. |
| **TLS** | Session resumption, cipher choice, ALPN, cert verification cost; follow `tls.Config` best practices. |
| **Connection observability** | Lifecycle visibility: DNS, dial, handshake, read/write, teardown; add tracing and metrics. |

### Examples (from [goperf.dev](https://goperf.dev))

**Socket: TCP_NODELAY** — disable Nagle for latency-sensitive TCP:

```go
if tcpConn, ok := conn.(*net.TCPConn); ok {
    tcpConn.SetNoDelay(true)
}
```

**DNS** — prefer pure-Go resolver for portability (no libc); use cgo only when needed for custom DNS:

```bash
export GODEBUG=netdns=go
```

Application-level DNS cache (e.g. with TTL) avoids repeated lookups when connecting to the same host.

**TLS: session resumption** — enable session tickets to avoid full handshakes on reconnect:

```go
tlsConfig := &tls.Config{
    SessionTicketsDisabled: false,
    // SessionTicketKey: [32]byte{...} — set and rotate for multi-instance
}
```

**TLS: cipher suites and ALPN** — prefer ECDHE + AES-GCM; advertise HTTP/2:

```go
tlsConfig := &tls.Config{
    CipherSuites: []uint16{
        tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
        tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
        tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
    },
    PreferServerCipherSuites: true,
    NextProtos:               []string{"h2", "http/1.1"},
}
```

**Force fresh DNS per request** (e.g. in Kubernetes when IPs change):

```go
DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
    return (&net.Dialer{}).DialContext(ctx, network, addr)
},
```
