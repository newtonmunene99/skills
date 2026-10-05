package store

import (
	"sync"
	"time"
)

type Order struct {
	OrderID    string    `json:"order_id"`
	CustomerID string    `json:"customer_id"`
	TotalUSD   string    `json:"total_usd"`
	PlacedAt   time.Time `json:"placed_at"`
}

type Store struct {
	mu     sync.RWMutex
	orders map[string]Order
}

func New() *Store {
	return &Store{orders: make(map[string]Order)}
}

func (s *Store) Get(id string) (Order, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	o, ok := s.orders[id]
	return o, ok
}

func (s *Store) Put(o Order) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.orders[o.OrderID] = o
}
