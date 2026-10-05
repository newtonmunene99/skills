package pricing

import "testing"

func TestTotal(t *testing.T) {
	if got := Total([]int64{1000}); got != 1160 {
		t.Fatalf("Total = %d, want 1160", got)
	}
}

func TestTotalEmpty(t *testing.T) {
	if got := Total(nil); got != 0 {
		t.Fatalf("Total(nil) = %d, want 0", got)
	}
}
