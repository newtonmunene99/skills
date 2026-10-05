# gateway

Outbound API gateway that throttles calls to partner APIs.

## About

`gateway` sits between our services and partner APIs. It applies a per-partner
token bucket so a burst from one service cannot exhaust a partner's quota for
everyone else.

## Installation

```bash
go get github.com/acme/gateway
```

## Usage

### Throttle a call

```go
b := ratelimit.New(10, 2) // 10-token burst, 2 tokens per second
if err := b.Allow(1); err != nil {
	return err // ErrLimitExceeded: drop or retry later
}
callPartner()
```

## License

Proprietary. Internal use only.
