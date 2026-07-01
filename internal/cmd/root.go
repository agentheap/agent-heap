package cmd

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "agent-heap",
	Short: "Agent Heap — Multi-chain yield optimization AI agent",
	Long: `Agent Heap is a multi-chain yield optimization AI agent.
It discovers, evaluates, and executes yield strategies across
Arbitrum, Base, and other EVM-compatible chains.`,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.AddCommand(startCmd)
	rootCmd.AddCommand(statusCmd)
	rootCmd.AddCommand(historyCmd)
	rootCmd.AddCommand(walletCmd)
	rootCmd.AddCommand(memoryCmd)
}
