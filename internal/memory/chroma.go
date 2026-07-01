package memory

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

// Entry represents a single Chroma vector memory entry.
type Entry struct {
	Action   string  `json:"action"`
	Protocol string  `json:"protocol"`
	Pool     string  `json:"pool"`
	Amount   float64 `json:"amount"`
	Reason   string  `json:"reason"`
	APY      float64 `json:"apy"`
	TVL      float64 `json:"tvl"`
}

// ChromaGetResponse maps the Chroma REST /api/v1/collections/{name}/get response.
type ChromaGetResponse struct {
	IDs       []string          `json:"ids"`
	Metadatas []json.RawMessage `json:"metadatas"`
	Documents []string          `json:"documents"`
}

// chromaURL returns the Chroma server URL from environment or default.
func chromaURL() string {
	if u := os.Getenv("CHROMA_URL"); u != "" {
		return strings.TrimRight(u, "/")
	}
	return "http://localhost:8000"
}

// collectionName returns the Chroma collection name.
func collectionName() string {
	if n := os.Getenv("CHROMA_COLLECTION"); n != "" {
		return n
	}
	return "agent_memory"
}

// Query fetches recent memory entries from Chroma's REST API.
// It uses the /api/v1/collections/{name}/get endpoint to retrieve all entries,
// then returns the last `limit` entries with their metadata parsed.
func Query(limit int) ([]Entry, error) {
	url := fmt.Sprintf("%s/api/v1/collections/%s/get", chromaURL(), collectionName())

	payload := map[string]interface{}{
		"limit": limit + 100, // fetch extra to handle filtering
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequest(http.MethodPost, url, strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("chroma request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("chroma returned status %d: %s", resp.StatusCode, string(respBody))
	}

	var result ChromaGetResponse
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("parse response: %w", err)
	}

	// Parse metadatas into Entry structs
	var entries []Entry
	for i, meta := range result.Metadatas {
		if len(meta) == 0 {
			continue
		}

		var e Entry
		if err := json.Unmarshal(meta, &e); err != nil {
			// Skip entries that can't be parsed
			continue
		}

		// Only include entries with at least an action
		if e.Action == "" {
			continue
		}

		entries = append(entries, e)

		// Track index to not exceed limit
		_ = i
	}

	// Take the last N entries
	if len(entries) > limit {
		entries = entries[len(entries)-limit:]
	}

	if entries == nil {
		entries = []Entry{}
	}

	return entries, nil
}

// HealthCheck pings the Chroma server to verify connectivity.
func HealthCheck() error {
	url := fmt.Sprintf("%s/api/v1/health", chromaURL())

	resp, err := http.DefaultClient.Get(url)
	if err != nil {
		return fmt.Errorf("chroma health check: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("chroma returned status %d", resp.StatusCode)
	}

	return nil
}
