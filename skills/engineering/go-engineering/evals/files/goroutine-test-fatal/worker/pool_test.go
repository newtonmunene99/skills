package worker

import (
	"testing"
	"time"
)

func mustRun(t *testing.T, p *Pool, job func() error) {
	if err := p.Run(job); err != nil {
		t.Fatalf("Run: %v", err)
	}
}

func TestPoolRunsJobsConcurrently(t *testing.T) {
	p, err := NewPool(4)
	if err != nil {
		t.Fatalf("NewPool: %v", err)
	}

	for i := 0; i < 10; i++ {
		go func() {
			mustRun(t, p, func() error { return nil })
		}()
	}
	for i := 0; i < 10; i++ {
		go func() {
			if err := p.Run(func() error { return nil }); err != nil {
				t.Fatal(err)
			}
		}()
	}

	time.Sleep(50 * time.Millisecond)
	if got := p.Done(); got != 20 {
		t.Fatalf("Done() = %d, want 20", got)
	}
}
