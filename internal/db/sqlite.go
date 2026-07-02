package db

import (
	"database/sql"
	"os"
	"sync"
	"time"

	_ "modernc.org/sqlite"
)

// Time alias for time.Time to allow mocking in tests.
type Time = time.Time

// Now returns the current UTC time. Tests may override via db.SetTimeNow().
var Now = func() Time { return time.Now().UTC() }

// Trade represents a single agent decision/trade.
type Trade struct {
	ID           int64
	StrategyID   int64
	Action       string
	Amount       float64
	Token        string
	TxHash       string
	GasCost      float64
	SimulatedPnL float64
	Timestamp    Time
}

// AgentState represents the agent's current operational state.
type AgentState struct {
	ID      int64
	Status  string
	LastRun Time
	Config  string // JSON blob
}

// TxLogEntry represents a transaction log entry for rate limiting.
type TxLogEntry struct {
	ID        int64
	TxHash    string
	Amount    float64
	Protocol  string
	Status    string
	Error     string
	Timestamp Time
}

var (
	mu     sync.Mutex
	dbPath string
)

func dbPathOrDefault() string {
	if dbPath != "" {
		return dbPath
	}
	return "agent-heap.db"
}

// Init initializes the database and creates tables if needed.
func Init() error {
	mu.Lock()
	defer mu.Unlock()
	return initDB()
}

func initDB() error {
	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return err
	}
	defer db.Close()

	schema := `
	CREATE TABLE IF NOT EXISTS trades (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		strategy_id INTEGER,
		action TEXT NOT NULL,
		amount REAL NOT NULL DEFAULT 0,
		token TEXT NOT NULL DEFAULT '',
		tx_hash TEXT,
		gas_cost REAL DEFAULT 0,
		simulated_pnl REAL DEFAULT 0,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS agent_state (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		status TEXT NOT NULL DEFAULT 'stopped',
		last_run DATETIME,
		config TEXT
	);

	CREATE TABLE IF NOT EXISTS heartbeats (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		ts DATETIME DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS tx_log (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		tx_hash TEXT,
		amount REAL DEFAULT 0,
		protocol TEXT,
		status TEXT DEFAULT 'pending',
		error TEXT,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
	);`

	_, err = db.Exec(schema)
	return err
}

// SaveTrade records a new trade entry.
func SaveTrade(action string, amount float64, token string, simulatedPnL float64) error {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec(
		`INSERT INTO trades (action, amount, token, simulated_pnl, timestamp) VALUES (?, ?, ?, ?, ?)`,
		action, amount, token, simulatedPnL, Now(),
	)
	return err
}

// GetAgentState returns the most recent agent state, or nil if none exists.
func GetAgentState() (*AgentState, error) {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return nil, err
	}
	defer db.Close()

	row := db.QueryRow(`SELECT id, status, last_run, config FROM agent_state ORDER BY id DESC LIMIT 1`)

	var state AgentState
	var lastRun sql.NullTime
	var config sql.NullString

	if err := row.Scan(&state.ID, &state.Status, &lastRun, &config); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}

	if lastRun.Valid {
		state.LastRun = lastRun.Time
	}
	if config.Valid {
		state.Config = config.String
	}

	return &state, nil
}

// SetAgentStatus sets the agent's operational status.
func SetAgentStatus(status string) error {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return err
	}
	defer db.Close()

	var count int
	if err := db.QueryRow(`SELECT COUNT(*) FROM agent_state`).Scan(&count); err != nil {
		return err
	}

	if count > 0 {
		_, err = db.Exec(`UPDATE agent_state SET status = ? WHERE id = (SELECT MAX(id) FROM agent_state)`, status)
	} else {
		_, err = db.Exec(`INSERT INTO agent_state (status, config) VALUES (?, '{}')`, status)
	}
	return err
}

// UpdateLastRun sets the last_run timestamp to now.
func UpdateLastRun() error {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return err
	}
	defer db.Close()

	var count int
	if err := db.QueryRow(`SELECT COUNT(*) FROM agent_state`).Scan(&count); err != nil {
		return err
	}

	now := Now()
	if count > 0 {
		_, err = db.Exec(`UPDATE agent_state SET last_run = ? WHERE id = (SELECT MAX(id) FROM agent_state)`, now)
	} else {
		_, err = db.Exec(`INSERT INTO agent_state (status, last_run, config) VALUES ('running', ?, '{}')`, now)
	}
	return err
}

// GetRecentTrades returns the most recent trades limited by n.
func GetRecentTrades(limit int) ([]Trade, error) {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return nil, err
	}
	defer db.Close()

	rows, err := db.Query(
		`SELECT id, action, amount, token, gas_cost, tx_hash, timestamp FROM trades ORDER BY id DESC LIMIT ?`,
		limit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var trades []Trade
	for rows.Next() {
		var t Trade
		var ts sql.NullTime
		var txHash sql.NullString
		if err := rows.Scan(&t.ID, &t.Action, &t.Amount, &t.Token, &t.GasCost, &txHash, &ts); err != nil {
			return nil, err
		}
		if ts.Valid {
			t.Timestamp = ts.Time
		}
		if txHash.Valid {
			t.TxHash = txHash.String
		}
		trades = append(trades, t)
	}

	if trades == nil {
		trades = []Trade{}
	}

	return trades, rows.Err()
}

// GetDailyTxVolume returns the total trade amount for today UTC.
func GetDailyTxVolume() (float64, error) {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return 0, err
	}
	defer db.Close()

	startOfDay := Now().Truncate(24 * time.Hour)
	var total sql.NullFloat64
	err = db.QueryRow(
		`SELECT SUM(amount) FROM trades WHERE timestamp >= ?`, startOfDay,
	).Scan(&total)
	if err != nil {
		return 0, err
	}
	if total.Valid {
		return total.Float64, nil
	}
	return 0, nil
}

// GetRecentTxCount returns the number of transactions in the last N hours.
func GetRecentTxCount(hours int) (int, error) {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return 0, err
	}
	defer db.Close()

	since := Now().Add(-time.Duration(hours) * time.Hour)
	var count int
	err = db.QueryRow(
		`SELECT COUNT(*) FROM trades WHERE timestamp >= ?`, since,
	).Scan(&count)
	if err != nil {
		return 0, err
	}
	return count, nil
}

// LogTx records a transaction attempt in tx_log.
func LogTx(hash, protocol, status, errorMsg string, amount float64) error {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec(
		`INSERT INTO tx_log (tx_hash, amount, protocol, status, error) VALUES (?, ?, ?, ?, ?)`,
		hash, amount, protocol, status, errorMsg,
	)
	return err
}

// GetTxCountSince returns the number of tx_log entries since the given time.
func GetTxCountSince(since Time) (int, error) {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return 0, err
	}
	defer db.Close()

	var count int
	err = db.QueryRow(`SELECT COUNT(*) FROM tx_log WHERE timestamp >= ?`, since).Scan(&count)
	if err != nil {
		return 0, err
	}
	return count, nil
}

// SaveHeartbeat records a heartbeat timestamp.
func SaveHeartbeat() error {
	mu.Lock()
	defer mu.Unlock()

	db, err := sql.Open("sqlite", dbPathOrDefault())
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec(`INSERT INTO heartbeats (ts) VALUES (?)`, Now())
	return err
}

// SetDBPath sets a custom database path for testing.
func SetDBPath(path string) {
	dbPath = path
}

// DBPath returns the configured database path.
func DBPath() string {
	return dbPathOrDefault()
}

func init() {
	if p := os.Getenv("DATABASE_URL"); p != "" {
		if len(p) > 9 && p[:9] == "sqlite://" {
			p = p[9:]
		}
		dbPath = p
	}
}
