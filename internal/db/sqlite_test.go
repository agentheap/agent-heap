package db

import (
	"database/sql"
	"path/filepath"
	"testing"
	"time"
)

func TestInit(t *testing.T) {
	path := tempDB(t)
	SetDBPath(path)

	if err := Init(); err != nil {
		t.Fatalf("Init() error = %v", err)
	}

	// Second call should be idempotent
	if err := Init(); err != nil {
		t.Fatalf("Init() second call error = %v", err)
	}

	// Verify tables exist
	database, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()

	tables := []string{"trades", "agent_state", "heartbeats"}
	for _, name := range tables {
		var n int
		err := database.QueryRow(`SELECT COUNT(*) FROM ` + name).Scan(&n)
		if err != nil {
			t.Errorf("table %q does not exist: %v", name, err)
		}
	}
}

func TestSaveAndGetRecentTrades(t *testing.T) {
	path := tempDB(t)
	SetDBPath(path)
	mustInit(t)

	trades, err := GetRecentTrades(10)
	if err != nil {
		t.Fatalf("GetRecentTrades on empty db: %v", err)
	}
	if len(trades) != 0 {
		t.Fatalf("expected 0 trades, got %d", len(trades))
	}

	if err := SaveTrade("deposit", 1.5, "USDC", 0.01); err != nil {
		t.Fatalf("SaveTrade: %v", err)
	}
	if err := SaveTrade("withdraw", 0.5, "USDC", 0); err != nil {
		t.Fatalf("SaveTrade: %v", err)
	}

	trades, err = GetRecentTrades(10)
	if err != nil {
		t.Fatalf("GetRecentTrades: %v", err)
	}
	if len(trades) != 2 {
		t.Fatalf("expected 2 trades, got %d", len(trades))
	}

	if trades[0].Action != "withdraw" {
		t.Errorf("expected newest first, got action=%q", trades[0].Action)
	}
	if trades[0].Amount != 0.5 {
		t.Errorf("amount got %f, want 0.5", trades[0].Amount)
	}
	if trades[0].Token != "USDC" {
		t.Errorf("token got %q, want USDC", trades[0].Token)
	}
	if trades[0].Timestamp.IsZero() {
		t.Error("expected non-zero timestamp")
	}

	if trades[1].Action != "deposit" {
		t.Errorf("expected second action=deposit, got %q", trades[1].Action)
	}
}

func TestGetRecentTradesLimit(t *testing.T) {
	path := tempDB(t)
	SetDBPath(path)
	mustInit(t)

	for i := 0; i < 5; i++ {
		if err := SaveTrade("deposit", float64(i), "USDC", 0); err != nil {
			t.Fatal(err)
		}
	}

	trades, err := GetRecentTrades(2)
	if err != nil {
		t.Fatalf("GetRecentTrades: %v", err)
	}
	if len(trades) != 2 {
		t.Fatalf("expected 2 trades, got %d", len(trades))
	}
}

func TestAgentStateLifecycle(t *testing.T) {
	path := tempDB(t)
	SetDBPath(path)
	mustInit(t)

	state, err := GetAgentState()
	if err != nil {
		t.Fatalf("GetAgentState on empty db: %v", err)
	}
	if state != nil {
		t.Fatal("expected nil state on empty db")
	}

	if err := SetAgentStatus("running"); err != nil {
		t.Fatalf("SetAgentStatus: %v", err)
	}

	state, err = GetAgentState()
	if err != nil {
		t.Fatalf("GetAgentState: %v", err)
	}
	if state == nil {
		t.Fatal("expected non-nil state")
	}
	if state.Status != "running" {
		t.Errorf("status = %q, want running", state.Status)
	}

	if err := SetAgentStatus("stopped"); err != nil {
		t.Fatalf("SetAgentStatus: %v", err)
	}

	state, err = GetAgentState()
	if err != nil {
		t.Fatalf("GetAgentState: %v", err)
	}
	if state.Status != "stopped" {
		t.Errorf("status = %q, want stopped", state.Status)
	}
}

func TestUpdateLastRun(t *testing.T) {
	path := tempDB(t)
	SetDBPath(path)
	mustInit(t)

	fakeNow := time.Date(2026, 7, 2, 12, 0, 0, 0, time.UTC)
	Now = func() time.Time { return fakeNow }
	defer func() { Now = time.Now }()

	if err := UpdateLastRun(); err != nil {
		t.Fatalf("UpdateLastRun: %v", err)
	}

	state, err := GetAgentState()
	if err != nil {
		t.Fatal(err)
	}
	if state.LastRun != fakeNow {
		t.Errorf("LastRun = %v, want %v", state.LastRun, fakeNow)
	}

	// Update again with a new time
	newTime := fakeNow.Add(time.Hour)
	Now = func() time.Time { return newTime }

	if err := UpdateLastRun(); err != nil {
		t.Fatal(err)
	}
	state, err = GetAgentState()
	if err != nil {
		t.Fatal(err)
	}
	if state.LastRun != newTime {
		t.Errorf("LastRun = %v, want %v", state.LastRun, newTime)
	}
}

func TestSaveHeartbeat(t *testing.T) {
	path := tempDB(t)
	SetDBPath(path)
	mustInit(t)

	if err := SaveHeartbeat(); err != nil {
		t.Fatalf("SaveHeartbeat: %v", err)
	}
	if err := SaveHeartbeat(); err != nil {
		t.Fatalf("SaveHeartbeat: %v", err)
	}

	database, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	defer database.Close()

	var count int
	if err := database.QueryRow(`SELECT COUNT(*) FROM heartbeats`).Scan(&count); err != nil {
		t.Fatal(err)
	}
	if count != 2 {
		t.Errorf("expected 2 heartbeats, got %d", count)
	}
}

func TestSetDBPath(t *testing.T) {
	dbPath = ""
	defer func() { dbPath = "" }()

	SetDBPath("/tmp/test-custom.db")
	got := DBPath()
	if got != "/tmp/test-custom.db" {
		t.Errorf("DBPath() = %q, want /tmp/test-custom.db", got)
	}
}

func TestDBPathDefault(t *testing.T) {
	dbPath = ""
	defer func() { dbPath = "" }()

	got := dbPathOrDefault()
	if got != "agent-heap.db" {
		t.Errorf("dbPathOrDefault() = %q, want agent-heap.db", got)
	}
}

// ── helpers ──────────────────────────────────────────────────────────

func tempDB(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	return filepath.Join(dir, "test.db")
}

func mustInit(t *testing.T) {
	t.Helper()
	if err := Init(); err != nil {
		t.Fatalf("Init() failed: %v", err)
	}
}
