package cmd

import (
	"testing"
	"time"

	"github.com/agentheap/agent-heap/internal/db"
)

func TestRootCommandHelp(t *testing.T) {
	rootCmd.SetArgs([]string{"--help"})
	err := rootCmd.Execute()
	if err != nil {
		t.Fatalf("Execute() error = %v", err)
	}
}

func TestRootCommandHasSubcommands(t *testing.T) {
	expected := []string{"start", "status", "history", "wallet", "memory"}
	for _, name := range expected {
		cmd, _, err := rootCmd.Find([]string{name})
		if err != nil {
			t.Errorf("subcommand %q not found: %v", name, err)
			continue
		}
		if cmd == nil {
			t.Errorf("subcommand %q is nil", name)
		}
	}
}

func TestStartCommandHasFlags(t *testing.T) {
	cmd, _, _ := rootCmd.Find([]string{"start"})
	if cmd == nil {
		t.Fatal("start command not found")
	}

	flag := cmd.Flags().Lookup("interval")
	if flag == nil {
		t.Fatal("--interval flag not found on start command")
	}
	if flag.DefValue != "21600" {
		t.Errorf("--interval default = %q, want 21600", flag.DefValue)
	}
}

func TestHistoryCommandHasFlags(t *testing.T) {
	cmd, _, _ := rootCmd.Find([]string{"history"})
	if cmd == nil {
		t.Fatal("history command not found")
	}

	flag := cmd.Flags().Lookup("limit")
	if flag == nil {
		t.Fatal("--limit flag not found on history command")
	}
	if flag.DefValue != "10" {
		t.Errorf("--limit default = %q, want 10", flag.DefValue)
	}
}

func TestWalletHasSubcommands(t *testing.T) {
	cmd, _, _ := rootCmd.Find([]string{"wallet"})
	if cmd == nil {
		t.Fatal("wallet command not found")
	}

	expected := []string{"generate", "balance", "new"}
	for _, name := range expected {
		sub, _, err := cmd.Find([]string{name})
		if err != nil {
			t.Errorf("wallet subcommand %q not found: %v", name, err)
			continue
		}
		if sub == nil {
			t.Errorf("wallet subcommand %q is nil", name)
		}
	}
}

func TestMemoryCommandHasFlags(t *testing.T) {
	cmd, _, _ := rootCmd.Find([]string{"memory"})
	if cmd == nil {
		t.Fatal("memory command not found")
	}

	flag := cmd.Flags().Lookup("last")
	if flag == nil {
		t.Fatal("--last flag not found on memory command")
	}
	if flag.DefValue != "10" {
		t.Errorf("--last default = %q, want 10", flag.DefValue)
	}
}

func TestFormatUptime(t *testing.T) {
	// Freeze time for deterministic output
	fakeNow := time.Date(2026, 7, 2, 12, 0, 0, 0, time.UTC)
	originalNow := db.Now
	db.Now = func() db.Time { return fakeNow }
	defer func() { db.Now = originalNow }()

	tests := []struct {
		name     string
		pastTime time.Time
		expected string
	}{
		{
			name:     "5 seconds",
			pastTime: fakeNow.Add(-5 * time.Second),
			expected: "5s",
		},
		{
			name:     "59 seconds",
			pastTime: fakeNow.Add(-59 * time.Second),
			expected: "59s",
		},
		{
			name:     "1 minute",
			pastTime: fakeNow.Add(-60 * time.Second),
			expected: "1m 0s",
		},
		{
			name:     "1 hour",
			pastTime: fakeNow.Add(-3600 * time.Second),
			expected: "1h 0m 0s",
		},
		{
			name:     "1h 1m 1s",
			pastTime: fakeNow.Add(-3661 * time.Second),
			expected: "1h 1m 1s",
		},
		{
			name:     "0 seconds",
			pastTime: fakeNow,
			expected: "0s",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := formatUptime(tt.pastTime)
			if got != tt.expected {
				t.Errorf("formatUptime() = %q, want %q", got, tt.expected)
			}
		})
	}
}
