// Package ratelimit implements a token bucket for throttling outbound calls.
//
// A Bucket starts full and refills continuously at a fixed rate. Callers ask
// for tokens with Allow, which returns ErrLimitExceeded when the bucket cannot
// cover the request, so the caller can drop or retry the call.
package ratelimit
