package cmd

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/heapchain/agent-heap/internal/agent"
	"github.com/heapchain/agent-heap/internal/db"
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

	// Initialize DB
	if err := db.Init(); err != nil {
		return fmt.Errorf("db init: %w", err)
	}

	// Set running state
	if err := db.SetAgentStatus("running"); err != nil {
		return fmt.Errorf("set status: %w", err)
	}

	// Signal handling
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	running := true

	// Heartbeat ticker
	heartbeatTick := time.NewTicker(30 * time.Second)
	defer heartbeatTick.Stop()

	// Loop interval ticker
	loopTick := time.NewTicker(time.Duration(interval) * time.Second)
	defer loopTick.Stop()

	// Run once immediately
	runAgentIteration()

	for running {
		select {
		case <-sigCh:
			fmt.Println("\nShutting down gracefully...")
			running = false

		case <-heartbeatTick.C:
			_ = db.SaveHeartbeat()

		case <-loopTick.C:
			runAgentIteration()
		}
	}

	_ = db.SetAgentStatus("stopped")
	fmt.Println("Agent stopped.")
	_ = db.SaveHeartbeat()
	return nil
}

func runAgentIteration() {
	fmt.Println("Running agent graph...")
	result, err := agent.Run()
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

	// Update last run timestamp
	_ = db.UpdateLastRun()
}
