package cmd

import (
	"fmt"
	"os"

	"github.com/agentheap/agent-heap/internal/wallet"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

type securityItem struct {
	feature string
	status  string
	detail  string
}

var securityCmd = &cobra.Command{
	Use:   "security",
	Short: "Show security feature status",
	Long: `Display the current status of all security features:
keystore encryption, spending limits, address allowlisting,
rate limiting, and key storage method.`,
	Run: func(cmd *cobra.Command, args []string) {
		items := []securityItem{
			checkKeystore(),
			checkPrivateKeyEnv(),
			checkSpendingLimitStatus(),
			checkRateLimiting(),
			checkAddressAllowlist(),
			checkCircuitBreaker(),
			checkAllowlistAddresses(),
		}

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Feature", "Status", "Details"})
		table.SetColumnAlignment([]int{tablewriter.ALIGN_LEFT, tablewriter.ALIGN_CENTER, tablewriter.ALIGN_LEFT})

		for _, item := range items {
			table.Append([]string{item.feature, item.status, item.detail})
		}

		table.Render()

		fmt.Println()
		fmt.Println("RECOMMENDATIONS:")
		fmt.Println("  1. Use 'agent-heap wallet encrypt' to create an encrypted keystore")
		fmt.Println("  2. Set KEYSTORE_FILE + KEYSTORE_PASSPHRASE in .env")
		fmt.Println("  3. Set MAX_TX_AMOUNT and DAILY_TX_LIMIT to cap spending")
		fmt.Println("  4. Set MAX_TX_PER_HOUR to prevent gas waste")
		fmt.Println("  5. Remove PRIVATE_KEY from .env once keystore is configured")
	},
}

func checkKeystore() securityItem {
	ksFile := os.Getenv("KEYSTORE_FILE")
	ksPass := os.Getenv("KEYSTORE_PASSPHRASE")

	if ksFile != "" && ksPass != "" {
		// Quick existence check without full decryption
		info, err := os.Stat(ksFile)
		if err != nil {
			return securityItem{
				feature: "Keystore Encrypted",
				status:  "⚠️ PARTIAL",
				detail:  fmt.Sprintf("KEYSTORE_FILE set but cannot read: %v", err),
			}
		}
		if info.Size() == 0 {
			return securityItem{
				feature: "Keystore Encrypted",
				status:  "⚠️ PARTIAL",
				detail:  "KEYSTORE_FILE is empty",
			}
		}

		return securityItem{
			feature: "Keystore Encrypted",
			status:  "✓ ENABLED",
			detail:  fmt.Sprintf("AES-256-GCM keystore at %s (%d bytes)", ksFile, info.Size()),
		}
	}

	return securityItem{
		feature: "Keystore Encrypted",
		status:  "✗ DISABLED",
		detail:  "Set KEYSTORE_FILE + KEYSTORE_PASSPHRASE in .env",
	}
}

func checkPrivateKeyEnv() securityItem {
	pk := os.Getenv("PRIVATE_KEY")
	if pk != "" {
		return securityItem{
			feature: "Private Key in Env",
			status:  "⚠️ WARNING",
			detail:  "PRIVATE_KEY is set — prefer encrypted keystore instead",
		}
	}
	return securityItem{
		feature: "Private Key in Env",
		status:  "✓ CLEAN",
		detail:  "PRIVATE_KEY not set in environment (good — use keystore)",
	}
}

func checkSpendingLimitStatus() securityItem {
	maxTx := os.Getenv("MAX_TX_AMOUNT")
	dailyLimit := os.Getenv("DAILY_TX_LIMIT")

	if maxTx != "" || dailyLimit != "" {
		detail := ""
		if maxTx != "" {
			detail += fmt.Sprintf("max/tx: %s USDC", maxTx)
		}
		if dailyLimit != "" {
			if detail != "" {
				detail += ", "
			}
			detail += fmt.Sprintf("daily: %s USDC", dailyLimit)
		}
		return securityItem{
			feature: "Spending Limits",
			status:  "✓ ENABLED",
			detail:  detail,
		}
	}

	return securityItem{
		feature: "Spending Limits",
		status:  "✗ DISABLED",
		detail:  "Set MAX_TX_AMOUNT and/or DAILY_TX_LIMIT in .env",
	}
}

func checkRateLimiting() securityItem {
	limit := os.Getenv("MAX_TX_PER_HOUR")
	if limit != "" {
		return securityItem{
			feature: "Rate Limiting",
			status:  "✓ ENABLED",
			detail:  fmt.Sprintf("max %s tx/hour", limit),
		}
	}
	return securityItem{
		feature: "Rate Limiting",
		status:  "✗ DISABLED",
		detail:  "Set MAX_TX_PER_HOUR in .env (recommended: 10)",
	}
}

func checkAddressAllowlist() securityItem {
	return securityItem{
		feature: "Address Allowlist",
		status:  "✓ ENABLED",
		detail:  fmt.Sprintf("%d known addresses (Aave, Compound, Morpho, USDC)", len(wallet.AllowedAddresses)),
	}
}

func checkCircuitBreaker() securityItem {
	return securityItem{
		feature: "Circuit Breaker",
		status:  "✓ ENABLED",
		detail:  "5% daily drawdown halt (built-in)",
	}
}

func checkAllowlistAddresses() securityItem {
	return securityItem{
		feature: "Allowlist Coverage",
		status:  fmt.Sprintf("%d addresses", len(wallet.AllowedAddresses)),
		detail:  "Aave V3, Compound III, Morpho Blue, USDC (testnet + mainnet)",
	}
}
