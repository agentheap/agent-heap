package cmd

import (
	"fmt"
	"os"

	"github.com/agentheap/agent-heap/internal/agent"
	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Run a single agent decision cycle",
	Long: `Execute one full agent cycle: collect yields from DeFiLlama,
analyze via LLM, generate a signal, execute (or simulate), and run buyback.
Prints the result and exits.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		result, err := agent.Run()
		if err != nil {
			return fmt.Errorf("agent run failed: %w", err)
		}

		// Extract fields from result
		tx := getMap(result, "tx_result")
		analysis := getMap(result, "analysis")
		buyback := getMap(result, "buyback_result")
		errs := getStrings(result, "errors")

		// ── Transaction result ──
		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Field", "Value"})
		table.SetColumnAlignment([]int{tablewriter.ALIGN_LEFT, tablewriter.ALIGN_LEFT})

		if tx != nil {
			table.Append([]string{"Action", stringOr(tx, "action", "—")})
			table.Append([]string{"Protocol", stringOr(tx, "protocol", "—")})
			table.Append([]string{"Pool", stringOr(tx, "pool", "—")})
			table.Append([]string{"Amount", fmt.Sprintf("%.4f", floatOr(tx, "amount", 0))})
			table.Append([]string{"Simulated", fmt.Sprintf("%v", boolOr(tx, "simulated", true))})
			table.Append([]string{"Reason", stringOr(tx, "reason", "—")})
			if hash, ok := tx["tx_hash"]; ok && hash != nil {
				table.Append([]string{"Tx Hash", fmt.Sprintf("%v", hash)})
			}
			if pnl, ok := tx["simulated_pnl"]; ok {
				table.Append([]string{"Sim PnL", fmt.Sprintf("%.4f", pnl)})
			}
			if errMsg, ok := tx["error"]; ok && errMsg != nil {
				table.Append([]string{"Error", fmt.Sprintf("%v", errMsg)})
			}
		} else {
			table.Append([]string{"Status", "No transaction (signal may be empty or circuit breaker tripped)"})
		}

		// ── Analysis details ──
		if analysis != nil {
			table.Append([]string{"Best Protocol", stringOr(analysis, "protocol", "—")})
			table.Append([]string{"Best APY", fmt.Sprintf("%.2f%%", floatOr(analysis, "apy", 0))})
		}

		// ── Buyback result ──
		if buyback != nil {
			status := stringOr(buyback, "status", "—")
			table.Append([]string{"Buyback", status})
		}

		// ── Errors ──
		if len(errs) > 0 {
			for i, e := range errs {
				label := "Error"
				if i > 0 {
					label = ""
				}
				table.Append([]string{label, e})
			}
		}

		table.Render()
		return nil
	},
}

// ── Result helpers ───────────────────────────────────────────────────

func getMap(m map[string]interface{}, key string) map[string]interface{} {
	if m == nil {
		return nil
	}
	v, ok := m[key]
	if !ok || v == nil {
		return nil
	}
	sub, ok := v.(map[string]interface{})
	if !ok {
		return nil
	}
	return sub
}

func stringOr(m map[string]interface{}, key, def string) string {
	if m == nil {
		return def
	}
	v, ok := m[key]
	if !ok || v == nil {
		return def
	}
	if s, ok := v.(string); ok {
		return s
	}
	return def
}

func floatOr(m map[string]interface{}, key string, def float64) float64 {
	if m == nil {
		return def
	}
	v, ok := m[key]
	if !ok || v == nil {
		return def
	}
	switch n := v.(type) {
	case float64:
		return n
	case int:
		return float64(n)
	case int64:
		return float64(n)
	default:
		return def
	}
}

func boolOr(m map[string]interface{}, key string, def bool) bool {
	if m == nil {
		return def
	}
	v, ok := m[key]
	if !ok || v == nil {
		return def
	}
	if b, ok := v.(bool); ok {
		return b
	}
	return def
}

func getStrings(m map[string]interface{}, key string) []string {
	if m == nil {
		return nil
	}
	v, ok := m[key]
	if !ok || v == nil {
		return nil
	}
	raw, ok := v.([]interface{})
	if !ok {
		return nil
	}
	result := make([]string, 0, len(raw))
	for _, item := range raw {
		if s, ok := item.(string); ok {
			result = append(result, s)
		}
	}
	return result
}
