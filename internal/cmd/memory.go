package cmd

import (
	"fmt"
	"os"

	"github.com/heapchain/agent-heap/internal/memory"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var memoryCmd = &cobra.Command{
	Use:   "memory",
	Short: "Show recent vector memory entries",
	Long:  `Query Chroma vector store directly via REST API and display recent entries.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		last, _ := cmd.Flags().GetInt("last")

		entries, err := memory.Query(last)
		if err != nil {
			fmt.Println("Could not connect to Chroma vector store")
			return nil
		}

		if len(entries) == 0 {
			fmt.Println("No memory entries yet")
			return nil
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"#", "Action", "Protocol", "Pool", "Amount", "Reason"})

		for i, e := range entries {
			reason := e.Reason
			if len(reason) > 50 {
				reason = reason[:50]
			}
			table.Append([]string{
				fmt.Sprintf("%d", i+1),
				e.Action,
				e.Protocol,
				e.Pool,
				fmt.Sprintf("%.4f", e.Amount),
				reason,
			})
		}

		table.Render()
		return nil
	},
}

func init() {
	memoryCmd.Flags().Int("last", 10, "Number of recent entries to show")
}
