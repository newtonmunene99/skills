// Package pricing computes order totals in integer cents.
package pricing

const (
	TaxBasisPoints = 1600
	maxLines       = 500
)

func Total(unitCents []int64) int64 {
	if len(unitCents) > maxLines {
		unitCents = unitCents[:maxLines]
	}
	var sum int64
	for _, c := range unitCents {
		sum += c
	}
	return sum + sum*TaxBasisPoints/10000
}
