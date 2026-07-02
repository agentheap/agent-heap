package cmd

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/agentheap/agent-heap/internal/db"
	"github.com/agentheap/agent-heap/internal/memory"
	"github.com/agentheap/agent-heap/internal/wallet"
	"github.com/ethereum/go-ethereum/ethclient"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

type healthResult struct {
	service string
	status  string
	detail  string
}

var healthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check agent service health",
	Long: `Ping all services (RPC, Chroma, SQLite, LLM, wallet) and
report their status in a table.`,
	Run: func(cmd *cobra.Command, args []string) {
		results := make([]healthResult, 0, 5)

		results = append(results, checkRPC())
		results = append(results, checkChroma())
		results = append(results, checkSQLite())
		results = append(results, checkLLM())
		results = append(results, checkWallet())

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Service", "Status", "Details"})
		table.SetColumnAlignment([]int{tablewriter.ALIGN_LEFT, tablewriter.ALIGN_CENTER, tablewriter.ALIGN_LEFT})

		for _, r := range results {
			table.Append([]string{r.service, r.status, r.detail})
		}

		table.Render()

		// Exit with non-zero if any service failed
		for _, r := range results {
			if r.status != "✓ OK" {
				os.Exit(1)
			}
		}
	},
}

func checkRPC() healthResult {
	rpcURL := os.Getenv("ARBITRUM_RPC")
	if rpcURL == "" {
		return healthResult{
			service: "RPC",
			status:  "⚠ SKIP",
			detail:  "ARBITRUM_RPC not set",
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	start := time.Now()
	client, err := ethclient.DialContext(ctx, rpcURL)
	if err != nil {
		return healthResult{
			service: "RPC",
			status:  "✗ FAIL",
			detail:  fmt.Sprintf("dial error: %v", err),
		}
	}
	defer client.Close()

	chainID, err := client.ChainID(ctx)
	elapsed := time.Since(start).Milliseconds()
	if err != nil {
		return healthResult{
			service: "RPC",
			status:  "✗ FAIL",
			detail:  fmt.Sprintf("chain id error: %v", err),
		}
	}

	return healthResult{
		service: "RPC",
		status:  "✓ OK",
		detail:  fmt.Sprintf("Chain %d @ %dms", chainID.Int64(), elapsed),
	}
}

func checkChroma() healthResult {
	err := memory.HealthCheck()
	if err != nil {
		return healthResult{
			service: "ChromaDB",
			status:  "✗ FAIL",
			detail:  fmt.Sprintf("%v", err),
		}
	}

	chromaURL := os.Getenv("CHROMA_URL")
	if chromaURL == "" {
		chromaURL = "http://localhost:8000"
	}
	return healthResult{
		service: "ChromaDB",
		status:  "✓ OK",
		detail:  chromaURL,
	}
}

func checkSQLite() healthResult {
	if err := db.Init(); err != nil {
		return healthResult{
			service: "SQLite",
			status:  "✗ FAIL",
			detail:  fmt.Sprintf("init error: %v", err),
		}
	}

	info, err := os.Stat(db.DBPath())
	if err != nil {
		return healthResult{
			service: "SQLite",
			status:  "✓ OK",
			detail:  db.DBPath(),
		}
	}

	return healthResult{
		service: "SQLite",
		status:  "✓ OK",
		detail:  fmt.Sprintf("%s (%.1fMB)", db.DBPath(), float64(info.Size())/1024/1024),
	}
}

func checkLLM() healthResult {
	model := os.Getenv("LLM_MODEL")
	if model == "" {
		return healthResult{
			service: "LLM",
			status:  "⚠ SKIP",
			detail:  "LLM_MODEL not set (uses APY fallback)",
		}
	}

	baseURL := os.Getenv("ANTHROPIC_BASE_URL")
	if baseURL != "" {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		req, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"/health", nil)
		if err == nil {
			resp, err := http.DefaultClient.Do(req)
			if err == nil {
				resp.Body.Close()
				if resp.StatusCode == http.StatusOK {
					return healthResult{
						service: "LLM",
						status:  "✓ OK",
						detail:  fmt.Sprintf("%s (proxy at %s)", model, baseURL),
					}
				}
			}
		}
	}

	return healthResult{
		service: "LLM",
		status:  "✓ OK",
		detail:  fmt.Sprintf("%s configured (unable to ping proxy)", model),
	}
}

func checkWallet() healthResult {
	key := os.Getenv("PRIVATE_KEY")
	if key == "" {
		return healthResult{
			service: "Wallet",
			status:  "⚠ SKIP",
			detail:  "PRIVATE_KEY not set",
		}
	}

	addr, err := wallet.PrivateKeyToAddress(key)
	if err != nil {
		return healthResult{
			service: "Wallet",
			status:  "✗ FAIL",
			detail:  fmt.Sprintf("invalid key: %v", err),
		}
	}

	rpc := os.Getenv("ARBITRUM_RPC")
	balanceDetail := ""
	if rpc != "" {
		result, err := wallet.CheckBalance(key, rpc)
		if err == nil {
			balanceDetail = fmt.Sprintf(" | %.4f ETH", result.BalanceETH)
		}
	}

	return healthResult{
		service: "Wallet",
		status:  "✓ OK",
		detail:  fmt.Sprintf("%s%s", addr, balanceDetail),
	}
}
