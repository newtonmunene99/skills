// Copied from an upstream semver package; keep in sync with upstream rather
// than editing here.
package semver

import "strings"

func Compare(a, b string) int {
	return strings.Compare(strings.TrimPrefix(a, "v"), strings.TrimPrefix(b, "v"))
}

func IsValid(v string) bool {
	return strings.HasPrefix(v, "v")
}
