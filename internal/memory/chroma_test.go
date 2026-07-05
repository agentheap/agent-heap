package memory

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestQueryReturnsEmptyOnEmptyServer(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if !strings.Contains(r.URL.Path, "/api/v2/collections/") {
			t.Errorf("unexpected path: %s", r.URL.Path)
		}
		resp := ChromaGetResponse{
			IDs:       []string{},
			Metadatas: []json.RawMessage{},
			Documents: []string{},
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer srv.Close()

	t.Setenv("CHROMA_URL", srv.URL)
	t.Setenv("CHROMA_COLLECTION", "test_collection")

	entries, err := Query(10)
	if err != nil {
		t.Fatalf("Query() error = %v", err)
	}
	if len(entries) != 0 {
		t.Errorf("expected 0 entries, got %d", len(entries))
	}
}

func TestQueryReturnsEntries(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		meta1 := json.RawMessage(`{"action":"deposit","protocol":"aave","pool":"USDC","amount":1.0,"reason":"high apy"}`)
		meta2 := json.RawMessage(`{"action":"deposit","protocol":"compound","pool":"USDC","amount":0.5,"reason":"low risk"}`)
		resp := ChromaGetResponse{
			IDs:       []string{"id1", "id2"},
			Metadatas: []json.RawMessage{meta1, meta2},
			Documents: []string{"doc1", "doc2"},
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer srv.Close()

	t.Setenv("CHROMA_URL", srv.URL)
	t.Setenv("CHROMA_COLLECTION", "test_collection")

	entries, err := Query(10)
	if err != nil {
		t.Fatalf("Query() error = %v", err)
	}
	if len(entries) != 2 {
		t.Fatalf("expected 2 entries, got %d", len(entries))
	}
	if entries[0].Action != "deposit" {
		t.Errorf("entries[0].Action = %q, want deposit", entries[0].Action)
	}
	if entries[0].Protocol != "aave" {
		t.Errorf("entries[0].Protocol = %q, want aave", entries[0].Protocol)
	}
	if entries[1].Protocol != "compound" {
		t.Errorf("entries[1].Protocol = %q, want compound", entries[1].Protocol)
	}
}

func TestQuerySkipsEmptyMetadata(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		meta1 := json.RawMessage(`{"action":"deposit","protocol":"aave","amount":1.0}`)
		emptyMeta := json.RawMessage(`{}`)
		resp := ChromaGetResponse{
			IDs:       []string{"id1", "id2"},
			Metadatas: []json.RawMessage{meta1, emptyMeta},
			Documents: []string{"doc1", "doc2"},
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer srv.Close()

	t.Setenv("CHROMA_URL", srv.URL)
	t.Setenv("CHROMA_COLLECTION", "test_collection")

	entries, err := Query(10)
	if err != nil {
		t.Fatalf("Query() error = %v", err)
	}
	if len(entries) != 1 {
		t.Errorf("expected 1 entry (skipped empty), got %d", len(entries))
	}
}

func TestQueryLimit(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req map[string]interface{}
		json.NewDecoder(r.Body).Decode(&req)
		limit, _ := req["limit"].(float64)
		// Server should request limit + 100 buffer
		if int(limit) != 110 {
			t.Errorf("expected limit 110, got %d", int(limit))
		}
		resp := ChromaGetResponse{
			IDs:       []string{},
			Metadatas: []json.RawMessage{},
			Documents: []string{},
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer srv.Close()

	t.Setenv("CHROMA_URL", srv.URL)
	t.Setenv("CHROMA_COLLECTION", "test_collection")

	_, err := Query(10)
	if err != nil {
		t.Fatalf("Query() error = %v", err)
	}
}

func TestQueryErrorReturnsEmpty(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"error":"internal error"}`))
	}))
	defer srv.Close()

	t.Setenv("CHROMA_URL", srv.URL)
	t.Setenv("CHROMA_COLLECTION", "test_collection")

	entries, err := Query(10)
	if err != nil {
		t.Fatalf("Query() error = %v", err)
	}
	if len(entries) != 0 {
		t.Errorf("expected 0 entries on fallback, got %d", len(entries))
	}
}

func TestHealthCheck(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	t.Setenv("CHROMA_URL", srv.URL)

	if err := HealthCheck(); err != nil {
		t.Fatalf("HealthCheck() error = %v", err)
	}
}

func TestHealthCheckFails(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	t.Setenv("CHROMA_URL", srv.URL)

	if err := HealthCheck(); err == nil {
		t.Error("expected error for 503, got nil")
	}
}

func TestChromaURLDefault(t *testing.T) {
	t.Setenv("CHROMA_URL", "")
	got := chromaURL()
	if got != "http://localhost:8000" {
		t.Errorf("chromaURL() = %q, want http://localhost:8000", got)
	}
}

func TestChromaURLFromEnv(t *testing.T) {
	t.Setenv("CHROMA_URL", "http://custom:9000/")
	got := chromaURL()
	if got != "http://custom:9000" {
		t.Errorf("chromaURL() = %q, want http://custom:9000", got)
	}
}

func TestCollectionNameDefault(t *testing.T) {
	t.Setenv("CHROMA_COLLECTION", "")
	got := collectionName()
	if got != "agent_memory" {
		t.Errorf("collectionName() = %q, want agent_memory", got)
	}
}

func TestCollectionNameFromEnv(t *testing.T) {
	t.Setenv("CHROMA_COLLECTION", "custom")
	got := collectionName()
	if got != "custom" {
		t.Errorf("collectionName() = %q, want custom", got)
	}
}
