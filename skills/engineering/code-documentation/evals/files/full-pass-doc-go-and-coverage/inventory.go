package inventory

import (
	"errors"
	"sync"
)

var ErrInsufficient = errors.New("inventory: insufficient stock")

type Item struct {
	SKU      string
	Qty      int
	Reserved int
}

func (i Item) Available() int { return i.Qty - i.Reserved }

type Store interface {
	Get(sku string) (Item, bool)
	Reserve(sku string, n int) error
}

// NewStore returns an empty in-memory Store that is safe for concurrent use.
func NewStore() Store {
	return &memStore{items: map[string]Item{}}
}

type memStore struct {
	mu    sync.Mutex
	items map[string]Item
}

func (m *memStore) Get(sku string) (Item, bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	it, ok := m.items[sku]
	return it, ok
}

func (m *memStore) Reserve(sku string, n int) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	return reserve(m.items, sku, n)
}

func reserve(items map[string]Item, sku string, n int) error {
	it := items[sku]
	if n <= 0 || it.Available() < n {
		return ErrInsufficient
	}
	it.Reserved += n
	items[sku] = it
	return nil
}
