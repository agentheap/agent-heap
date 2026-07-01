package wallet

import (
	"context"
	"crypto/ecdsa"
	"fmt"
	"math/big"
	"time"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/ethclient"
	"github.com/ethereum/go-ethereum/params"
)

// Wallet holds a generated EVM wallet's key material.
type Wallet struct {
	PrivateKey string
	Address    string
}

// BalanceResult holds an RPC balance query result.
type BalanceResult struct {
	Address    string
	BalanceWei *big.Int
	BalanceETH float64
}

// Generate creates a fresh EVM wallet using crypto.GenerateKey().
func Generate() (*Wallet, error) {
	privateKey, err := crypto.GenerateKey()
	if err != nil {
		return nil, fmt.Errorf("generate key: %w", err)
	}

	privateKeyHex := fmt.Sprintf("0x%x", crypto.FromECDSA(privateKey))
	address := crypto.PubkeyToAddress(privateKey.PublicKey).Hex()

	return &Wallet{
		PrivateKey: privateKeyHex,
		Address:    address,
	}, nil
}

// PrivateKeyToAddress derives the address from a hex-encoded private key.
func PrivateKeyToAddress(privateKeyHex string) (string, error) {
	// Strip 0x prefix if present
	key := privateKeyHex
	if len(key) > 2 && key[:2] == "0x" {
		key = key[2:]
	}

	privateKey, err := crypto.HexToECDSA(key)
	if err != nil {
		return "", fmt.Errorf("parse private key: %w", err)
	}

	address := crypto.PubkeyToAddress(privateKey.PublicKey).Hex()
	return address, nil
}

// CheckBalance queries an RPC endpoint for the ETH balance of a wallet.
func CheckBalance(privateKeyHex, rpcURL string) (*BalanceResult, error) {
	address, err := PrivateKeyToAddress(privateKeyHex)
	if err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	client, err := ethclient.DialContext(ctx, rpcURL)
	if err != nil {
		return nil, fmt.Errorf("dial rpc: %w", err)
	}
	defer client.Close()

	balanceWei, err := client.BalanceAt(ctx, common.HexToAddress(address), nil)
	if err != nil {
		return nil, fmt.Errorf("balance at: %w", err)
	}

	balanceEth := new(big.Float).Quo(
		new(big.Float).SetInt(balanceWei),
		new(big.Float).SetFloat64(params.Ether),
	)

	balanceEthF64, _ := balanceEth.Float64()

	return &BalanceResult{
		Address:    address,
		BalanceWei: balanceWei,
		BalanceETH: balanceEthF64,
	}, nil
}

// SignTransaction signs a transaction with the given private key.
func SignTransaction(privateKeyHex string, tx *types.Transaction, chainID *big.Int) (*types.Transaction, error) {
	privateKey, err := crypto.HexToECDSA(privateKeyHex)
	if err != nil {
		return nil, fmt.Errorf("parse private key: %w", err)
	}

	signer := types.LatestSignerForChainID(chainID)
	signedTx, err := types.SignTx(tx, signer, privateKey)
	if err != nil {
		return nil, fmt.Errorf("sign tx: %w", err)
	}

	return signedTx, nil
}

// PublicKeyToAddress derives an address from an ECDSA public key.
func PublicKeyToAddress(pub *ecdsa.PublicKey) string {
	return crypto.PubkeyToAddress(*pub).Hex()
}
