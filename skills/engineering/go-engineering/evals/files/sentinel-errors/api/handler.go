// Package api serves orders over HTTP.
package api

import (
	"encoding/json"
	"net/http"
	"strings"

	"example.com/orders/service"
)

// Handler serves GET /orders/{id}.
type Handler struct {
	Orders *service.Orders
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/orders/")
	o, err := h.Orders.Lookup(id)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			http.Error(w, "no such order", http.StatusNotFound)
			return
		}
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	if err := json.NewEncoder(w).Encode(o); err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
	}
}
