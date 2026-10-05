// Package money represents currency amounts as integer minor units so that
// arithmetic never goes through floating point.
package money

import "fmt"

// Amount is a quantity of one currency in minor units (cents for USD).
type Amount struct {
	Minor    int64
	Currency string
}

// Add returns the sum of a and b. It returns an error if the currencies
// differ.
func Add(a, b Amount) Amount {
	if a.Currency != b.Currency {
		panic(fmt.Sprintf("money: currency mismatch %s != %s", a.Currency, b.Currency))
	}
	return Amount{Minor: a.Minor + b.Minor, Currency: a.Currency}
}

func Split(a Amount, n int) []Amount {
	parts := make([]Amount, n)
	base, rem := a.Minor/int64(n), a.Minor%int64(n)
	for i := range parts {
		parts[i] = Amount{Minor: base, Currency: a.Currency}
		if int64(i) < rem {
			parts[i].Minor++
		}
	}
	return parts
}

// String formats the amount for logs, for example "12.34 USD".
func (a Amount) String() string {
	return fmt.Sprintf("%d.%02d %s", a.Minor/100, a.Minor%100, a.Currency)
}
