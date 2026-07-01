package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/agentheap/agent-heap/internal/wallet"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var walletCmd = &cobra.Command{
	Use:   "wallet",
	Short: "Wallet management commands",
	Long:  `Generate EVM wallets, check balances, and manage wallet files.`,
}

func init() {
	walletCmd.AddCommand(walletGenerateCmd)
	walletCmd.AddCommand(walletBalanceCmd)
	walletCmd.AddCommand(walletNewCmd)

	walletGenerateCmd.Flags().StringP("output", "o", "", "Write wallet JSON to file")
	walletNewCmd.Flags().StringP("output", "o", "", "Write wallet JSON to file")
}

var walletGenerateCmd = &cobra.Command{
	Use:   "generate",
	Short: "Generate a fresh EVM wallet",
	Long: `Generate a fresh EVM wallet using go-ethereum.
Optionally write an encrypted JSON keystore to --output.
Prints address and funding instructions.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		output, _ := cmd.Flags().GetString("output")

		networkLabel := "Arbitrum Sepolia (testnet)"
		chainID := int64(421614)
		rpc := "https://sepolia-rollup.arbitrum.io/rpc"
		if strings.EqualFold(os.Getenv("ARBITRUM_NETWORK"), "mainnet") {
			networkLabel = "Arbitrum One (mainnet)"
			chainID = 42161
			rpc = "https://arb1.arbitrum.io/rpc"
		}

		fmt.Printf("Generating wallet for %s...\n", networkLabel)

		w, err := wallet.Generate()
		if err != nil {
			return fmt.Errorf("generate wallet: %w", err)
		}

		fmt.Printf("✓ Wallet address: %s\n", w.Address)

		if output != "" {
			info := map[string]interface{}{
				"address":     w.Address,
				"private_key": w.PrivateKey,
				"network":     networkLabel,
				"chain_id":    chainID,
				"rpc_url":     rpc,
			}
			data, _ := json.MarshalIndent(info, "", "  ")
			if err := os.WriteFile(output, data, 0600); err != nil {
				return fmt.Errorf("write wallet: %w", err)
			}
			absPath, _ := os.Getwd()
			fmt.Printf("✓ Wallet saved to: %s/%s\n", absPath, output)
			fmt.Println("   ⚠ Keep this file secure!")
		}

		printFundingInstructions(w.Address, networkLabel)
		return nil
	},
}

var walletNewCmd = &cobra.Command{
	Use:   "new",
	Short: "Alias for 'wallet generate'",
	Long:  `Alias for 'wallet generate' — creates a new wallet and prints funding instructions.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		output, _ := cmd.Flags().GetString("output")

		networkLabel := "Arbitrum Sepolia (testnet)"
		chainID := int64(421614)
		rpc := "https://sepolia-rollup.arbitrum.io/rpc"
		if strings.EqualFold(os.Getenv("ARBITRUM_NETWORK"), "mainnet") {
			networkLabel = "Arbitrum One (mainnet)"
			chainID = 42161
			rpc = "https://arb1.arbitrum.io/rpc"
		}

		fmt.Printf("Generating wallet for %s...\n", networkLabel)

		w, err := wallet.Generate()
		if err != nil {
			return fmt.Errorf("generate wallet: %w", err)
		}

		fmt.Printf("✓ Wallet address: %s\n", w.Address)

		if output != "" {
			info := map[string]interface{}{
				"address":     w.Address,
				"private_key": w.PrivateKey,
				"network":     networkLabel,
				"chain_id":    chainID,
				"rpc_url":     rpc,
			}
			data, _ := json.MarshalIndent(info, "", "  ")
			if err := os.WriteFile(output, data, 0600); err != nil {
				return fmt.Errorf("write wallet: %w", err)
			}
			absPath, _ := os.Getwd()
			fmt.Printf("✓ Wallet saved to: %s/%s\n", absPath, output)
		}

		printFundingInstructions(w.Address, networkLabel)
		return nil
	},
}

var walletBalanceCmd = &cobra.Command{
	Use:   "balance",
	Short: "Check the balance of the configured wallet",
	Long: `Read PRIVATE_KEY from environment, derive the address,
and query the configured RPC for ETH balance.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		privateKey := os.Getenv("PRIVATE_KEY")
		if privateKey == "" {
			fmt.Println("Error: PRIVATE_KEY not set")
			fmt.Println("\nSet PRIVATE_KEY in your environment to check balance.")
			return nil
		}

		rpc := os.Getenv("ARBITRUM_RPC")
		if rpc == "" {
			rpc = "https://sepolia-rollup.arbitrum.io/rpc"
		}

		networkLabel := "Arbitrum Sepolia"
		if strings.EqualFold(os.Getenv("ARBITRUM_NETWORK"), "mainnet") {
			networkLabel = "Arbitrum One"
		}

		result, err := wallet.CheckBalance(privateKey, rpc)
		if err != nil {
			return fmt.Errorf("check balance: %w", err)
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Asset", "Value"})
		table.Append([]string{"Address", result.Address})
		table.Append([]string{"ETH", fmt.Sprintf("%.6f", result.BalanceETH)})
		table.SetCaption(true, fmt.Sprintf("Wallet Balance (%s)", networkLabel))
		table.Render()

		return nil
	},
}

func printFundingInstructions(address, networkLabel string) {
	isMainnet := strings.Contains(strings.ToLower(networkLabel), "mainnet")
	fmt.Println()
	fmt.Println("NEXT STEPS:")

	if isMainnet {
		fmt.Println("")
		fmt.Println("╔══════════════════════════════════════════╗")
		fmt.Println("║        MAINNET FUNDING INSTRUCTIONS      ║")
		fmt.Println("╚══════════════════════════════════════════╝")
		fmt.Println()
		fmt.Println("⚠  THIS IS REAL MONEY. Be careful!")
		fmt.Println()
		fmt.Println("To fund your wallet, send ETH and USDC to:")
		fmt.Println(" ", address)
		fmt.Println()
		fmt.Println("1. Buy ETH on any exchange (Coinbase, Binance, Kraken)")
		fmt.Println("2. Withdraw to the Arbitrum One network (not Ethereum L1)")
		fmt.Println("   https://bridge.arbitrum.io/")
		fmt.Println("Minimum: ~0.01 ETH for gas + USDC for deposits")
	} else {
		fmt.Println()
		fmt.Println("╔══════════════════════════════════════════╗")
		fmt.Println("║       FUNDING INSTRUCTIONS (TESTNET)     ║")
		fmt.Println("╚══════════════════════════════════════════╝")
		fmt.Println()
		fmt.Println("1. Fund with testnet ETH from Arbitrum Sepolia faucet:")
		fmt.Println("   • QuickNode: https://faucet.quicknode.com/arbitrum/sepolia")
		fmt.Println("   • Alchemy:   https://www.alchemy.com/faucets/arbitrum-sepolia")
		fmt.Println("   • Chainlink: https://faucets.chain.link/arbitrum-sepolia")
		fmt.Println("   • GetBlock:  https://getblock.io/faucet/arb-sepolia/")
		fmt.Println()
		fmt.Println("2. Get testnet USDC via Circle faucet:")
		fmt.Println("   • https://faucet.circle.com/")
		fmt.Println()
		fmt.Println("3. Set PRIVATE_KEY in .env to this wallet's private key")
		fmt.Println("4. Run 'agent-heap wallet balance' to verify funding")
	}
}
