package cmd

import (
	"fmt"
	"os"

	"github.com/agentheap/agent-heap/internal/db"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var historyCmd = &cobra.Command{
	Use:   "history",
	Short: "Show recent agent decisions",
	Long:  `Query recent trades table and display the last N decisions.`,
	Run: func(cmd *cobra.Command, args []string) {
		limit, _ := cmd.Flags().GetInt("limit")

		if err := db.Init(); err != nil {
			fmt.Printf("Error: db init: %v\n", err)
			return
		}

		trades, err := db.GetRecentTrades(limit)
		if err != nil {
			fmt.Printf("Error: get trades: %v\n", err)
			return
		}

		if len(trades) == 0 {
			fmt.Println("No history yet")
			return
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"ID", "Action", "Token", "Amount", "Gas", "Tx Hash", "Timestamp"})

		for _, t := range trades {
			ts := ""
			if !t.Timestamp.IsZero() {
				ts = t.Timestamp.Format("2006-01-02 15:04:05")
			}

			txHash := ""
			if t.TxHash != "" {
				if len(t.TxHash) > 16 {
					txHash = t.TxHash[:16] + "..."
				} else {
					txHash = t.TxHash
				}
			}

			gasStr := ""
			if t.GasCost > 0 {
				gasStr = fmt.Sprintf("%.6f", t.GasCost)
			}

			table.Append([]string{
				fmt.Sprintf("%d", t.ID),
				t.Action,
				t.Token,
				fmt.Sprintf("%.4f", t.Amount),
				gasStr,
				txHash,
				ts,
			})
		}

		table.Render()
	},
}

func init() {
	historyCmd.Flags().Int("limit", 10, "Number of recent trades to show")
}
