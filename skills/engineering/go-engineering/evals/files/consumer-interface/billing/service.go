// Package billing charges customers and issues invoices.
package billing

import (
	"context"
	"errors"
	"fmt"
	"time"

	"example.com/shop/storage"
)

// Service bills customers.
type Service struct {
	store storage.Store
	now   func() time.Time
}

// NewService returns a Service that uses store.
func NewService(store storage.Store) *Service {
	return &Service{store: store, now: time.Now}
}

// Charge debits amount from the customer and records an invoice.
func (s *Service) Charge(ctx context.Context, customerID string, amount int64) error {
	if amount <= 0 {
		return errors.New("amount must be positive")
	}
	c, err := s.store.GetCustomer(ctx, customerID)
	if err != nil {
		return fmt.Errorf("get customer %s: %w", customerID, err)
	}
	if err := s.store.UpdateBalance(ctx, c.ID, -amount); err != nil {
		return fmt.Errorf("debit customer %s: %w", c.ID, err)
	}
	inv := storage.Invoice{
		ID:         fmt.Sprintf("%s-%d", c.ID, s.now().UnixNano()),
		CustomerID: c.ID,
		Amount:     amount,
		IssuedAt:   s.now(),
	}
	if err := s.store.CreateInvoice(ctx, inv); err != nil {
		return fmt.Errorf("create invoice for %s: %w", c.ID, err)
	}
	return nil
}
