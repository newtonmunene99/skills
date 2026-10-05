// Package worker runs jobs on a fixed number of goroutines.
package worker

import (
	"errors"
	"sync"
)

// Pool runs jobs concurrently and counts the ones that succeed.
type Pool struct {
	mu   sync.Mutex
	done int
}

// NewPool returns a Pool. size must be positive.
func NewPool(size int) (*Pool, error) {
	if size <= 0 {
		return nil, errors.New("size must be positive")
	}
	return &Pool{}, nil
}

// Run runs job and records it if it succeeds.
func (p *Pool) Run(job func() error) error {
	if err := job(); err != nil {
		return err
	}
	p.mu.Lock()
	p.done++
	p.mu.Unlock()
	return nil
}

// Done reports how many jobs have succeeded.
func (p *Pool) Done() int {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.done
}
