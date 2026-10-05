// Package syncer copies records from the upstream API into the local cache.
package syncer

import (
	"context"
	"encoding/json"
	"fmt"
)

// Record is one upstream record.
type Record struct {
	ID   string `json:"id"`
	Body string `json:"body"`
}

// Sync writes records to put until ctx is cancelled.
//
// Marshalling errors are returned straight away; the sync is not retried.
func Sync(ctx context.Context, records []Record, put func(key string, val []byte) error) error {
	for _, r := range records {
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("sync cancelled: %w", err)
		}
		b, err := json.Marshal(r)
		if err != nil {
			return fmt.Errorf("marshalling record %s: %w", r.ID, err)
		}
		if err := put(r.ID, b); err != nil {
			return fmt.Errorf("put %s: %w", r.ID, err)
		}
	}
	return nil
}
