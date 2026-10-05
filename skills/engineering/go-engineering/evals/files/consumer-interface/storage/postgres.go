// Package storage is the shop's Postgres data layer.
package storage

import (
	"context"
	"database/sql"
	"time"
)

// Customer is a shop customer.
type Customer struct {
	ID      string
	Email   string
	Balance int64
}

// Invoice is a bill sent to a customer.
type Invoice struct {
	ID         string
	CustomerID string
	Amount     int64
	IssuedAt   time.Time
}

// Store is everything the shop can do with its database.
type Store interface {
	GetCustomer(ctx context.Context, id string) (Customer, error)
	ListCustomers(ctx context.Context) ([]Customer, error)
	CreateCustomer(ctx context.Context, c Customer) error
	DeleteCustomer(ctx context.Context, id string) error
	UpdateBalance(ctx context.Context, id string, delta int64) error
	CreateInvoice(ctx context.Context, inv Invoice) error
	ListInvoices(ctx context.Context, customerID string) ([]Invoice, error)
	Ping(ctx context.Context) error
}

type postgresStore struct {
	db *sql.DB
}

// NewStore returns a Store backed by db.
func NewStore(db *sql.DB) Store {
	return &postgresStore{db: db}
}

func (s *postgresStore) GetCustomer(ctx context.Context, id string) (Customer, error) {
	var c Customer
	err := s.db.QueryRowContext(ctx,
		`SELECT id, email, balance FROM customers WHERE id = $1`, id,
	).Scan(&c.ID, &c.Email, &c.Balance)
	return c, err
}

func (s *postgresStore) ListCustomers(ctx context.Context) ([]Customer, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT id, email, balance FROM customers`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Customer
	for rows.Next() {
		var c Customer
		if err := rows.Scan(&c.ID, &c.Email, &c.Balance); err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, rows.Err()
}

func (s *postgresStore) CreateCustomer(ctx context.Context, c Customer) error {
	_, err := s.db.ExecContext(ctx,
		`INSERT INTO customers (id, email, balance) VALUES ($1, $2, $3)`, c.ID, c.Email, c.Balance)
	return err
}

func (s *postgresStore) DeleteCustomer(ctx context.Context, id string) error {
	_, err := s.db.ExecContext(ctx, `DELETE FROM customers WHERE id = $1`, id)
	return err
}

func (s *postgresStore) UpdateBalance(ctx context.Context, id string, delta int64) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE customers SET balance = balance + $2 WHERE id = $1`, id, delta)
	return err
}

func (s *postgresStore) CreateInvoice(ctx context.Context, inv Invoice) error {
	_, err := s.db.ExecContext(ctx,
		`INSERT INTO invoices (id, customer_id, amount, issued_at) VALUES ($1, $2, $3, $4)`,
		inv.ID, inv.CustomerID, inv.Amount, inv.IssuedAt)
	return err
}

func (s *postgresStore) ListInvoices(ctx context.Context, customerID string) ([]Invoice, error) {
	rows, err := s.db.QueryContext(ctx,
		`SELECT id, customer_id, amount, issued_at FROM invoices WHERE customer_id = $1`, customerID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Invoice
	for rows.Next() {
		var inv Invoice
		if err := rows.Scan(&inv.ID, &inv.CustomerID, &inv.Amount, &inv.IssuedAt); err != nil {
			return nil, err
		}
		out = append(out, inv)
	}
	return out, rows.Err()
}

func (s *postgresStore) Ping(ctx context.Context) error {
	return s.db.PingContext(ctx)
}
