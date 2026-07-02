package cmd

import (
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/agentheap/agent-heap/internal/agent"
	"github.com/agentheap/agent-heap/internal/db"
	"github.com/spf13/cobra"
)

var startCmd = &cobra.Command{
	Use:   "start",
	Short: "Start the agent loop",
	Long: `Start the agent decision loop. Runs indefinitely until interrupted.
Writes heartbeat every 30s and calls the Python agent graph as a subprocess
on each iteration.`,
	RunE: runStart,
}

func init() {
	startCmd.Flags().Int("interval", 21600, "Loop interval in seconds")
}

func runStart(cmd *cobra.Command, args []string) error {
	interval, _ := cmd.Flags().GetInt("interval")
	if interval < 1 {
		return fmt.Errorf("interval must be >= 1")
	}

	fmt.Println("Agent Heap starting...")
	fmt.Printf("Interval: %ds | Ctrl+C to stop\n", interval)

	if err := db.Init(); err != nil {
		return fmt.Errorf("db init: %w", err)
	}
	if err := db.SetAgentStatus("running"); err != nil {
		return fmt.Errorf("set status: %w", err)
	}

	// Signal handling — buffered so we don't miss a signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	running := true
	var mu sync.Mutex

	heartbeatTick := time.NewTicker(30 * time.Second)
	defer heartbeatTick.Stop()

	loopTick := time.NewTicker(time.Duration(interval) * time.Second)
	defer loopTick.Stop()

	// Run once immediately in a goroutine so Ctrl+C works even if it hangs
	go func() {
		mu.Lock()
		runAgentIteration()
		mu.Unlock()
	}()

	for running {
		select {
		case <-sigCh:
			fmt.Println("\nShutting down gracefully...")
			running = false

		case <-heartbeatTick.C:
			_ = db.SaveHeartbeat()

		case <-loopTick.C:
			go func() {
				mu.Lock()
				defer mu.Unlock()
				if !running {
					return
				}
				runAgentIteration()
			}()
		}
	}

	_ = db.SetAgentStatus("stopped")
	fmt.Println("Agent stopped.")
	_ = db.SaveHeartbeat()
	return nil
}

func runAgentIteration() {
	fmt.Println("Running agent graph...")
	result, _, err := agent.RunWithKey()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	ts := time.Now().UTC().Format(time.RFC3339)
	fmt.Printf("%s Agent run complete\n", ts)

	if tx, ok := result["tx_result"].(map[string]interface{}); ok {
		action, _ := tx["action"].(string)
		protocol, _ := tx["protocol"].(string)
		pool, _ := tx["pool"].(string)
		amount, _ := tx["amount"].(float64)

		fmt.Printf("  Action: %s | Protocol: %s | Pool: %s\n", action, protocol, pool)

		_ = db.SaveTrade(action, amount, pool, 0)
	}

	_ = db.UpdateLastRun()
}
