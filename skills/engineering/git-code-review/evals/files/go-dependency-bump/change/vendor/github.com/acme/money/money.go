// Package money provides integer-cent arithmetic.
package money

import "errors"

// Cents is an amount in minor units.
type Cents int64

// RoundingMode selects how fractional cents are resolved.
type RoundingMode int

const (
	HalfUp RoundingMode = iota
	HalfEven
)

// ErrUnknownMode is returned by Round for a RoundingMode it does not support.
var ErrUnknownMode = errors.New("money: unknown rounding mode")

// Round resolves a fractional amount, given in hundredths of a cent, to whole cents.
func Round(hundredths int64, mode RoundingMode) (Cents, error) {
	if mode != HalfUp && mode != HalfEven {
		return 0, ErrUnknownMode
	}
	q, r := hundredths/100, hundredths%100
	switch {
	case r > 50, r == 50 && (mode == HalfUp || q%2 != 0):
		q++
	}
	return Cents(q), nil
}
