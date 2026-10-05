package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/acme/sales/services/orders-api/store"
)

func main() {
	s := store.New()
	http.HandleFunc("GET /v1/orders/{id}", func(w http.ResponseWriter, r *http.Request) {
		o, ok := s.Get(r.PathValue("id"))
		if !ok {
			http.NotFound(w, r)
			return
		}
		_ = json.NewEncoder(w).Encode(o)
	})
	addr := os.Getenv("ORDERS_API_ADDR")
	if addr == "" {
		addr = ":8080"
	}
	log.Fatal(http.ListenAndServe(addr, nil))
}
