// Package config loads and saves the agent's settings file.
package config

import (
	"encoding/json"
	"fmt"
	"os"
)

// Config is the agent's on-disk configuration.
type Config struct {
	ServerURL string `json:"server_url"`
	Token     string `json:"token"`
	Interval  int    `json:"interval_seconds"`
}

// Load reads the config at path.
func Load(path string) (Config, error) {
	var c Config
	b, err := os.ReadFile(path)
	if err != nil {
		return c, fmt.Errorf("read config: %w", err)
	}
	if err := json.Unmarshal(b, &c); err != nil {
		return c, fmt.Errorf("parse config: %w", err)
	}
	return c, nil
}

// Save writes c to path. The file is shared with the ops group, so it is
// kept at 0640.
func Save(path string, c Config) error {
	b, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return fmt.Errorf("encode config: %w", err)
	}
	if err := os.WriteFile(path, b, 0o640); err != nil {
		return fmt.Errorf("write config: %w", err)
	}
	return nil
}
