package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

// knownSecrets lists env vars whose values should be masked when displayed.
var knownSecrets = map[string]bool{
	"PRIVATE_KEY":            true,
	"OPENAI_API_KEY":         true,
	"ANTHROPIC_API_KEY":      true,
	"GEMINI_API_KEY":         true,
	"GROQ_API_KEY":           true,
	"MISTRAL_API_KEY":        true,
	"TOGETHER_API_KEY":       true,
	"ANTHROPIC_AUTH_TOKEN":   true,
}

var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Manage environment configuration",
	Long: `Manage .env configuration file. Lists, gets, and sets environment
variables used by Agent Heap. Values are read from the current environment
(which includes .env if loaded).`,
}

var configListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all configuration values",
	Long:  `Show all known Agent Heap configuration keys and their current values. Secret values are masked.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		allKeys := knownConfigKeys()

		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Variable", "Value", "Set"})
		table.SetColumnAlignment([]int{tablewriter.ALIGN_LEFT, tablewriter.ALIGN_LEFT, tablewriter.ALIGN_CENTER})

		for _, key := range allKeys {
			val := os.Getenv(key)
			isSet := val != ""
			displayVal := val
			if isSet && knownSecrets[key] {
				displayVal = maskValue(val)
			}
			if !isSet {
				displayVal = "(not set)"
			}

			setMarker := " "
			if isSet {
				setMarker = "✓"
			}

			table.Append([]string{key, displayVal, setMarker})
		}

		table.Render()
		return nil
	},
}

var configGetCmd = &cobra.Command{
	Use:   "get <key>",
	Short: "Get a configuration value",
	Long:  `Show the current value of a single configuration variable.`,
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		key := args[0]
		val := os.Getenv(key)

		displayVal := val
		if val != "" && knownSecrets[key] {
			displayVal = maskValue(val)
		}

		if val == "" {
			fmt.Printf("%s = (not set)\n", key)
		} else {
			fmt.Printf("%s = %s\n", key, displayVal)
		}
		return nil
	},
}

var configSetCmd = &cobra.Command{
	Use:   "set <key> <value>",
	Short: "Set a configuration value",
	Long: `Set a configuration variable in the .env file.
Creates .env if it doesn't exist. Updates the value if the key already exists.`,
	Args: cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		key := args[0]
		value := args[1]

		envPath := ".env"
		data, err := os.ReadFile(envPath)
		if err != nil {
			if !os.IsNotExist(err) {
				return fmt.Errorf("read .env: %w", err)
			}
			// File doesn't exist, create it
			data = []byte{}
		}

		lines := strings.Split(string(data), "\n")
		found := false
		for i, line := range lines {
			trimmed := strings.TrimSpace(line)
			if trimmed == "" || strings.HasPrefix(trimmed, "#") {
				continue
			}
			parts := strings.SplitN(trimmed, "=", 2)
			if len(parts) == 2 && strings.TrimSpace(parts[0]) == key {
				lines[i] = key + "=" + value
				found = true
				break
			}
		}

		if !found {
			lines = append(lines, key+"="+value)
		}

		output := strings.Join(lines, "\n") + "\n"
		if err := os.WriteFile(envPath, []byte(output), 0644); err != nil {
			return fmt.Errorf("write .env: %w", err)
		}

		// Also set in current environment so it takes effect immediately
		os.Setenv(key, value)

		displayKey := key
		displayVal := value
		if knownSecrets[key] {
			displayVal = maskValue(value)
		}

		fmt.Printf("✓ %s = %s\n", displayKey, displayVal)
		return nil
	},
}

func init() {
	configCmd.AddCommand(configListCmd)
	configCmd.AddCommand(configGetCmd)
	configCmd.AddCommand(configSetCmd)
}

// knownConfigKeys returns all known Agent Heap configuration keys in alphabetical order.
func knownConfigKeys() []string {
	return []string{
		"ANTHROPIC_API_KEY",
		"ANTHROPIC_AUTH_TOKEN",
		"ANTHROPIC_BASE_URL",
		"ARBITRUM_NETWORK",
		"ARBITRUM_RPC",
		"BASE_RPC",
		"CAPITAL",
		"CHROMA_COLLECTION",
		"CHROMA_URL",
		"DATABASE_URL",
		"GEMINI_API_KEY",
		"GROQ_API_KEY",
		"LLM_MODEL",
		"MISTRAL_API_KEY",
		"OPENAI_API_KEY",
		"PRIVATE_KEY",
		"TOGETHER_API_KEY",
	}
}

// maskValue returns a masked version of a secret value.
// Shows first 4 and last 4 characters, masking the middle.
func maskValue(val string) string {
	if len(val) <= 8 {
		return "****"
	}

	// Strip 0x prefix for hex keys when masking
	display := val
	if strings.HasPrefix(display, "0x") {
		display = display[2:]
	}

	if len(display) <= 8 {
		return "****"
	}

	return display[:4] + "..." + display[len(display)-4:]
}
