package cmd

import (
	"fmt"
	"os"

	"github.com/agentheap/agent-heap/internal/db"
	"github.com/agentheap/agent-heap/internal/wallet"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show agent state and heartbeat",
	Long:  `Read agent state + heartbeat from SQLite and display current status.`,
	Run: func(cmd *cobra.Command, args []string) {
		if err := db.Init(); err != nil {
			fmt.Printf("Error: db init: %v\n", err)
			return
		}

		state, err := db.GetAgentState()
		if err != nil {
			fmt.Printf("Error: get state: %v\n", err)
			return
		}

		status := "never run"
		lastRun := "N/A"
		uptime := "N/A"

		if state != nil {
			status = state.Status
			if !state.LastRun.IsZero() {
				lastRun = state.LastRun.Format("2006-01-02 15:04:05 UTC")
				uptime = formatUptime(state.LastRun)
			}
		}

		// ── Agent state ──
		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Field", "Value"})
		table.SetColumnAlignment([]int{tablewriter.ALIGN_LEFT, tablewriter.ALIGN_LEFT})
		table.Append([]string{"Status", status})
		table.Append([]string{"Last Run", lastRun})
		table.Append([]string{"Uptime", uptime})

		// ── Wallet ──
		key := os.Getenv("PRIVATE_KEY")
		if key != "" {
			addr, err := wallet.PrivateKeyToAddress(key)
			if err == nil {
				table.Append([]string{"Wallet", addr})

				// Try balance check
				rpc := os.Getenv("ARBITRUM_RPC")
				if rpc != "" {
					result, err := wallet.CheckBalance(key, rpc)
					if err == nil {
						table.Append([]string{"ETH Balance", fmt.Sprintf("%.6f ETH", result.BalanceETH)})
					}
				}
			}
		} else {
			table.Append([]string{"Wallet", "not configured"})
		}

		// ── Database ──
		info, err := os.Stat(db.DBPath())
		if err == nil {
			sizeMB := float64(info.Size()) / 1024 / 1024
			table.Append([]string{"DB Size", fmt.Sprintf("%.1f MB", sizeMB)})
		}

		table.Render()
	},
}

func formatUptime(t db.Time) string {
	d := db.Now().Sub(t)
	h := int(d.Hours())
	m := int(d.Minutes()) % 60
	s := int(d.Seconds()) % 60

	if h > 0 {
		return fmt.Sprintf("%dh %dm %ds", h, m, s)
	}
	if m > 0 {
		return fmt.Sprintf("%dm %ds", m, s)
	}
	return fmt.Sprintf("%ds", s)
}
