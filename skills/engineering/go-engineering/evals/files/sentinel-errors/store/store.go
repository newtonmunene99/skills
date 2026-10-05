// Package store keeps orders in memory.
package store

import (
	"errors"
	"fmt"
	"sync"
)

// Order is a customer order.
type Order struct {
	ID     string
	Amount int64
}

// Store holds orders by ID.
type Store struct {
	mu     sync.Mutex
	orders map[string]Order
}

// New returns an empty Store.
func New() *Store {
	return &Store{orders: make(map[string]Order)}
}

// Get returns the order with the given ID.
func (s *Store) Get(id string) (Order, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	o, ok := s.orders[id]
	if !ok {
		return Order{}, fmt.Errorf("no order with id %s", id)
	}
	return o, nil
}

// Put saves an order.
func (s *Store) Put(o Order) error {
	if o.ID == "" {
		return errors.New("Order ID is empty")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.orders[o.ID] = o
	return nil
}
