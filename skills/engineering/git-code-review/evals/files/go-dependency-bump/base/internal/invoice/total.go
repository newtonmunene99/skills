// Package invoice computes invoice totals.
package invoice

import "github.com/acme/money"

// Line is one invoice line, priced in hundredths of a cent.
type Line struct {
	Qty           int64
	UnitHundredth int64
}

// Total sums the lines and rounds half-even to whole cents.
func Total(lines []Line) money.Cents {
	var sum int64
	for _, l := range lines {
		sum += l.Qty * l.UnitHundredth
	}
	return money.Round(sum, money.HalfEven)
}
