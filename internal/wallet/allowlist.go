package wallet

import (
	"fmt"
	"os"
	"strings"
)

// Known protocol addresses for Arbitrum — matches agent/nodes/abi/__init__.py
var (
	// Mainnet addresses (Arbitrum One, chain ID 42161)
	AavePoolMainnet       = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
	CompoundCometMainnet  = "0xA5eD225DD425849A5252b4eB2300Fb654d12bbf0"
	MorphoBlueMainnet     = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
	USDCMainnet           = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

	// Testnet addresses (Arbitrum Sepolia, chain ID 421614)
	AavePoolSepolia      = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
	CompoundCometSepolia = "0x1b7E8Fb38e734FD41E73A94F2779982F73eF3706"
	MorphoBlueSepolia    = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
	USDSepolia           = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"
)

// mainnetAddresses contains only Arbitrum One addresses.
var mainnetAddresses = []string{
	strings.ToLower(AavePoolMainnet),
	strings.ToLower(CompoundCometMainnet),
	strings.ToLower(MorphoBlueMainnet),
	strings.ToLower(USDCMainnet),
}

// testnetAddresses contains only Arbitrum Sepolia addresses.
var testnetAddresses = []string{
	strings.ToLower(AavePoolSepolia),
	strings.ToLower(CompoundCometSepolia),
	strings.ToLower(MorphoBlueSepolia),
	strings.ToLower(USDSepolia),
}

// AllowedAddresses contains all addresses across both networks (for display).
var AllowedAddresses = append(mainnetAddresses, testnetAddresses...)

// isMainnet returns true if the current network is mainnet.
func isMainnet() bool {
	return strings.EqualFold(os.Getenv("ARBITRUM_NETWORK"), "mainnet")
}

// activeAllowlist returns the address list for the current network.
func activeAllowlist() []string {
	if isMainnet() {
		return mainnetAddresses
	}
	return testnetAddresses
}

// IsAllowedAddress checks if an address is a known protocol or token address
// for the CURRENT network. Comparison is case-insensitive.
func IsAllowedAddress(addr string) bool {
	lower := strings.ToLower(addr)
	for _, allowed := range activeAllowlist() {
		if lower == allowed {
			return true
		}
	}
	return false
}

// ValidateRecipient checks that a recipient address is in the allowlist
// for the current network.
func ValidateRecipient(recipient string) error {
	if !IsAllowedAddress(recipient) {
		network := "testnet"
		if isMainnet() {
			network = "mainnet"
		}
		return fmt.Errorf("address %s is not in the allowlist for %s — refusing to send", recipient, network)
	}
	return nil
}

// ProtocolAddresses returns the mainnet address map for protocol names.
func ProtocolAddresses() map[string]string {
	return map[string]string{
		"aave":     AavePoolMainnet,
		"compound": CompoundCometMainnet,
		"morpho":   MorphoBlueMainnet,
	}
}

// SepoliaAddresses returns the testnet address map.
func SepoliaAddresses() map[string]string {
	return map[string]string{
		"aave":     AavePoolSepolia,
		"compound": CompoundCometSepolia,
		"morpho":   MorphoBlueSepolia,
	}
}

// Check if the environment is set to mainnet, used for initialization.
var _ = isMainnet
