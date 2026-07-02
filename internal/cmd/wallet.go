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
	Long:  `Generate EVM wallets, check balances, encrypt keys, and manage wallet files.`,
}

func init() {
	walletCmd.AddCommand(walletGenerateCmd)
	walletCmd.AddCommand(walletBalanceCmd)
	walletCmd.AddCommand(walletNewCmd)
	walletCmd.AddCommand(walletEncryptCmd)

	walletGenerateCmd.Flags().StringP("output", "o", "", "Write wallet JSON to file")
	walletGenerateCmd.Flags().Bool("encrypt", false, "Encrypt wallet with passphrase (creates keystore)")
	walletGenerateCmd.Flags().String("passphrase", "", "Passphrase for encryption (required with --encrypt)")
	walletNewCmd.Flags().StringP("output", "o", "", "Write wallet JSON to file")
	walletNewCmd.Flags().Bool("encrypt", false, "Encrypt wallet with passphrase (creates keystore)")
	walletNewCmd.Flags().String("passphrase", "", "Passphrase for encryption (required with --encrypt)")
	walletEncryptCmd.Flags().StringP("output", "o", "", "Output file for encrypted keystore")
	walletEncryptCmd.Flags().String("passphrase", "", "Passphrase for encryption (required)")
}

func networkConfig() (label string, chainID int64, rpc string) {
	label = "Arbitrum Sepolia (testnet)"
	chainID = int64(421614)
	rpc = "https://sepolia-rollup.arbitrum.io/rpc"
	if strings.EqualFold(os.Getenv("ARBITRUM_NETWORK"), "mainnet") {
		label = "Arbitrum One (mainnet)"
		chainID = 42161
		rpc = "https://arb1.arbitrum.io/rpc"
	}
	return
}

var walletGenerateCmd = &cobra.Command{
	Use:   "generate",
	Short: "Generate a fresh EVM wallet",
	Long: `Generate a fresh EVM wallet using go-ethereum.
Use --encrypt --passphrase <pass> to create an encrypted keystore.
Without --encrypt, writes plaintext JSON (not recommended for production).`,
	RunE: func(cmd *cobra.Command, args []string) error {
		output, _ := cmd.Flags().GetString("output")
		encrypt, _ := cmd.Flags().GetBool("encrypt")
		passphrase, _ := cmd.Flags().GetString("passphrase")

		networkLabel, chainID, rpc := networkConfig()
		fmt.Printf("Generating wallet for %s...\n", networkLabel)

		if encrypt && passphrase == "" {
			return fmt.Errorf("--passphrase is required with --encrypt")
		}

		if encrypt {
			keystoreJSON, addr, err := wallet.GenerateEncrypted(passphrase)
			if err != nil {
				return fmt.Errorf("generate encrypted wallet: %w", err)
			}

			fmt.Printf("✓ Wallet address: %s\n", addr)
			fmt.Println("✓ Encrypted with AES-256-GCM (scrypt key derivation)")

			if output != "" {
				if err := os.WriteFile(output, keystoreJSON, 0600); err != nil {
					return fmt.Errorf("write keystore: %w", err)
				}
				fmt.Printf("✓ Encrypted keystore saved to: %s\n", output)
				fmt.Println("   ⚠ Keep this file AND your passphrase secure!")
				fmt.Println("   Without the passphrase, the wallet cannot be recovered.")
			} else {
				fmt.Println(string(keystoreJSON))
			}

			printFundingInstructions(addr, networkLabel)
			return nil
		}

		// Plaintext mode (default)
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
			fmt.Printf("✓ Wallet saved to: %s\n", output)
			fmt.Println("   ⚠ This file contains your raw private key!")
			fmt.Println("   Use 'agent-heap wallet encrypt' to secure it.")
		}

		printFundingInstructions(w.Address, networkLabel)
		return nil
	},
}

var walletEncryptCmd = &cobra.Command{
	Use:   "encrypt <key-file>",
	Short: "Encrypt an existing private key file",
	Long: `Read a private key from a JSON file or raw hex string,
encrypt it with a passphrase, and write an encrypted keystore.
Supports --output and --passphrase flags.`,
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		output, _ := cmd.Flags().GetString("output")
		passphrase, _ := cmd.Flags().GetString("passphrase")

		if passphrase == "" {
			return fmt.Errorf("--passphrase is required")
		}

		// Read input file
		inputPath := args[0]
		data, err := os.ReadFile(inputPath)
		if err != nil {
			return fmt.Errorf("read input: %w", err)
		}

		// Try to extract private key from JSON
		privateKeyHex := strings.TrimSpace(string(data))

		// If it's JSON, try to extract private_key field
		if len(data) > 0 && data[0] == '{' {
			var keyData map[string]interface{}
			if err := json.Unmarshal(data, &keyData); err == nil {
				// Check if this is a keystore (has ciphertext, not private_key)
				if _, isKeystore := keyData["ciphertext"]; isKeystore {
					return fmt.Errorf("input %s appears to be an encrypted keystore, not a raw key\nProvide the original private key file (plain hex or JSON with 'private_key' field)", inputPath)
				}
				if pk, ok := keyData["private_key"].(string); ok {
					privateKeyHex = strings.TrimSpace(pk)
				}
			}
		}

		// Validate the key
		addr, err := wallet.PrivateKeyToAddress(privateKeyHex)
		if err != nil {
			return fmt.Errorf("invalid private key in %s: %w", inputPath, err)
		}

		// Encrypt
		keystoreJSON, err := wallet.EncryptKey(privateKeyHex, passphrase)
		if err != nil {
			return fmt.Errorf("encrypt key: %w", err)
		}

		if output != "" {
			if err := os.WriteFile(output, keystoreJSON, 0600); err != nil {
				return fmt.Errorf("write keystore: %w", err)
			}
			fmt.Printf("✓ Encrypted keystore written to: %s\n", output)
		} else {
			fmt.Println(string(keystoreJSON))
		}

		fmt.Printf("✓ Address: %s\n", addr)
		fmt.Println("✓ Encryption: AES-256-GCM with scrypt key derivation")
		fmt.Println()
		fmt.Println("NEXT STEPS:")
		fmt.Printf("  Set KEYSTORE_FILE=%s and KEYSTORE_PASSPHRASE=<your-passphrase> in .env\n", output)
		fmt.Println("  The agent will load the key from the encrypted keystore instead of PRIVATE_KEY.")

		return nil
	},
}

var walletNewCmd = &cobra.Command{
	Use:   "new",
	Short: "Alias for 'wallet generate'",
	Long:  `Alias for 'wallet generate' — creates a new wallet and prints funding instructions.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Forward to generate command logic with same flags
		return walletGenerateCmd.RunE(cmd, args)
	},
}

var walletBalanceCmd = &cobra.Command{
	Use:   "balance",
	Short: "Check the balance of the configured wallet",
	Long: `Read PRIVATE_KEY (or KEYSTORE_FILE) from environment, derive the address,
and query the configured RPC for ETH balance.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		privateKey := os.Getenv("PRIVATE_KEY")

		// Try keystore if PRIVATE_KEY not set
		if privateKey == "" {
			ksFile := os.Getenv("KEYSTORE_FILE")
			ksPass := os.Getenv("KEYSTORE_PASSPHRASE")
			if ksFile != "" && ksPass != "" {
				data, err := os.ReadFile(ksFile)
				if err != nil {
					return fmt.Errorf("read keystore: %w", err)
				}
				var err2 error
				privateKey, _, err2 = wallet.LoadPrivateKeyFromReader(data, ksPass)
				if err2 != nil {
					return fmt.Errorf("decrypt keystore: %w", err2)
				}
			}
		}

		if privateKey == "" {
			fmt.Println("Error: No private key found")
			fmt.Println("\nSet PRIVATE_KEY in your environment, or set KEYSTORE_FILE + KEYSTORE_PASSPHRASE.")
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
		fmt.Println()
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
		fmt.Println("3. Set KEYSTORE_FILE + KEYSTORE_PASSPHRASE in .env (preferred) or PRIVATE_KEY")
		fmt.Println("4. Run 'agent-heap wallet balance' to verify funding")
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
		fmt.Println("2. Get testnet USDC via Circle faucet:")
		fmt.Println("   • https://faucet.circle.com/")
		fmt.Println()
		fmt.Println("3. Set KEYSTORE_FILE + KEYSTORE_PASSPHRASE in .env (preferred) or PRIVATE_KEY")
		fmt.Println("4. Run 'agent-heap wallet balance' to verify funding")
	}
}
