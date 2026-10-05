package ratelimit

import (
	"math"
	"sync"
	"time"
)

// Bucket is a token bucket. It is safe for concurrent use.
type Bucket struct {
	mu       sync.Mutex
	tokens   float64
	capacity float64
	refill   float64
	last     time.Time
}

// New returns a full Bucket holding capacity tokens that refills at
// refillPerSecond tokens per second.
func New(capacity, refillPerSecond float64) *Bucket {
	return &Bucket{
		tokens:   capacity,
		capacity: capacity,
		refill:   refillPerSecond,
		last:     time.Now(),
	}
}

// Allow takes n tokens from the bucket. It returns ErrLimitExceeded if fewer
// than n tokens are available, in which case no tokens are taken.
func (b *Bucket) Allow(n float64) time.Duration {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.advance(time.Now())
	if b.tokens < n {
		missing := n - b.tokens
		return time.Duration(missing / b.refill * float64(time.Second))
	}
	b.tokens -= n
	return 0
}

// advance adds the tokens refilled since the last call, capped at capacity.
// The caller must hold b.mu.
func (b *Bucket) advance(now time.Time) {
	elapsed := now.Sub(b.last).Seconds()
	b.tokens = math.Min(b.capacity, b.tokens+elapsed*b.refill)
	b.last = now
}
