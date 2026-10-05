// Package fx converts amounts between currencies.
package fx

import (
	"strconv"

	"github.com/acme/money"
)

// Convert applies a decimal exchange rate, given as a string, to an amount in cents.
func Convert(amount money.Cents, rate string) money.Cents {
	r, _ := strconv.ParseFloat(rate, 64)
	hundredths := int64(float64(amount) * r * 100)
	return money.Round(hundredths, money.HalfUp)
}
