package cmd

import (
	"fmt"
	"os"

	"github.com/heapchain/agent-heap/internal/db"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var historyCmd = &cobra.Command{
	Use:   "history",
	Short: "Show recent agent decisions",
	Long:  `Query recent trades table and display the last N decisions.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		limit, _ := cmd.Flags().GetInt("limit")

		if err := db.Init(); err != nil {
			return fmt.Errorf("db init: %w", err)
		}

		trades, err := db.GetRecentTrades(limit)
		if err != nil {
			return fmt.Errorf("get trades: %w", err)
		}

		if len(trades) == 0 {
			fmt.Println("No history yet")
			return nil
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"ID", "Action", "Token", "Amount", "Timestamp"})

		for _, t := range trades {
			ts := ""
			if !t.Timestamp.IsZero() {
				ts = t.Timestamp.Format("2006-01-02 15:04:05")
			}
			table.Append([]string{
				fmt.Sprintf("%d", t.ID),
				t.Action,
				t.Token,
				fmt.Sprintf("%.4f", t.Amount),
				ts,
			})
		}

		table.Render()
		return nil
	},
}

func init() {
	historyCmd.Flags().Int("limit", 10, "Number of recent trades to show")
}
