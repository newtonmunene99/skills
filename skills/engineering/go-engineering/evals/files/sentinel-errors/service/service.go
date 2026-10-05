// Package service holds the order business logic.
package service

import (
	"fmt"

	"example.com/orders/store"
)

// Orders looks orders up and applies business rules.
type Orders struct {
	Store *store.Store
}

// Lookup returns the order with the given ID.
func (s *Orders) Lookup(id string) (store.Order, error) {
	o, err := s.Store.Get(id)
	if err != nil {
		return store.Order{}, fmt.Errorf("lookup failed for %s: %v", id, err)
	}
	return o, nil
}
