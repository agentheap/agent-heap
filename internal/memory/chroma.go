package memory

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
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

// ChromaGetResponse maps the Chroma REST /api/v2/collections/{name}/get response.
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

// Query fetches recent memory entries via the Python chromadb client.
// Falls back from the REST API to a Python subprocess if the REST call fails.
func Query(limit int) ([]Entry, error) {
	// Try REST API first (v2)
	entries, err := queryREST(limit)
	if err == nil {
		return entries, nil
	}

	// Fall back to Python chromadb client
	return queryPython(limit)
}

// queryREST tries to fetch entries via Chroma v2 REST API.
func queryREST(limit int) ([]Entry, error) {
	url := fmt.Sprintf("%s/api/v2/collections/%s/get", chromaURL(), collectionName())

	payload := map[string]interface{}{
		"limit": limit + 100,
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
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("chroma returned status %d", resp.StatusCode)
	}

	var result ChromaGetResponse
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("parse response: %w", err)
	}

	return parseEntries(result, limit)
}

// queryPython queries ChromaDB via the Python chromadb client as a subprocess.
func queryPython(limit int) ([]Entry, error) {
	script := fmt.Sprintf(`
import json, sys
try:
    import chromadb
    client = chromadb.HttpClient(host='localhost', port=8000)
    try:
        col = client.get_collection('agent_memory')
    except Exception:
        col = client.get_or_create_collection('agent_memory')
    results = col.get(limit=%d)
    entries = []
    for i, meta in enumerate(results.get('metadatas', []) or []):
        if meta:
            entries.append(meta)
    print(json.dumps(entries))
except Exception as e:
    print(json.dumps([]))
`, limit)

	cmd := exec.Command("python3", "-c", script)
	output, err := cmd.Output()
	if err != nil {
		return []Entry{}, nil
	}

	var rawEntries []map[string]interface{}
	if err := json.Unmarshal(output, &rawEntries); err != nil {
		return []Entry{}, nil
	}

	entries := make([]Entry, 0, len(rawEntries))
	for _, r := range rawEntries {
		e := Entry{}
		if action, ok := r["action"].(string); ok {
			e.Action = action
		}
		if protocol, ok := r["protocol"].(string); ok {
			e.Protocol = protocol
		}
		if pool, ok := r["pool"].(string); ok {
			e.Pool = pool
		}
		if amount, ok := r["amount"].(float64); ok {
			e.Amount = amount
		}
		if reason, ok := r["reason"].(string); ok {
			e.Reason = reason
		}
		if apy, ok := r["apy"].(float64); ok {
			e.APY = apy
		}
		if tvl, ok := r["tvl"].(float64); ok {
			e.TVL = tvl
		}
		if e.Action != "" {
			entries = append(entries, e)
		}
	}

	// Take last N
	if len(entries) > limit {
		entries = entries[len(entries)-limit:]
	}

	return entries, nil
}

// parseEntries converts a ChromaGetResponse into Entry structs.
func parseEntries(result ChromaGetResponse, limit int) ([]Entry, error) {
	var entries []Entry
	for _, meta := range result.Metadatas {
		if len(meta) == 0 {
			continue
		}

		var e Entry
		if err := json.Unmarshal(meta, &e); err != nil {
			continue
		}

		if e.Action == "" {
			continue
		}

		entries = append(entries, e)
	}

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
	url := fmt.Sprintf("%s/api/v2/heartbeat", chromaURL())

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
