package cmd

import (
	"fmt"
	"os"

	"github.com/agentheap/agent-heap/internal/db"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show agent state and heartbeat",
	Long:  `Read agent state + heartbeat from SQLite and display current status.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		if err := db.Init(); err != nil {
			return fmt.Errorf("db init: %w", err)
		}

		state, err := db.GetAgentState()
		if err != nil {
			return fmt.Errorf("get state: %w", err)
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

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Field", "Value"})
		table.Append([]string{"Status", status})
		table.Append([]string{"Last Run", lastRun})
		table.Append([]string{"Uptime", uptime})
		table.Render()

		return nil
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
