package wallet

import (
	"strings"
	"testing"

	"github.com/ethereum/go-ethereum/crypto"
)

func TestGenerate(t *testing.T) {
	w, err := Generate()
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}
	if w == nil {
		t.Fatal("Generate() returned nil")
	}
	if w.Address == "" {
		t.Error("Address is empty")
	}
	if w.PrivateKey == "" {
		t.Error("PrivateKey is empty")
	}
	if !strings.HasPrefix(w.PrivateKey, "0x") {
		t.Errorf("PrivateKey %q does not start with 0x", w.PrivateKey)
	}
	if !strings.HasPrefix(w.Address, "0x") {
		t.Errorf("Address %q does not start with 0x", w.Address)
	}
	if len(w.PrivateKey) != 66 { // 0x + 64 hex chars
		t.Errorf("PrivateKey length = %d, want 66", len(w.PrivateKey))
	}
	if len(w.Address) != 42 { // 0x + 40 hex chars
		t.Errorf("Address length = %d, want 42", len(w.Address))
	}
}

func TestGenerateUniqueKeys(t *testing.T) {
	w1, _ := Generate()
	w2, _ := Generate()
	if w1.PrivateKey == w2.PrivateKey {
		t.Error("two Generate() calls returned the same private key")
	}
	if w1.Address == w2.Address {
		t.Error("two Generate() calls returned the same address")
	}
}

func TestPrivateKeyToAddress(t *testing.T) {
	w, err := Generate()
	if err != nil {
		t.Fatal(err)
	}

	addr, err := PrivateKeyToAddress(w.PrivateKey)
	if err != nil {
		t.Fatalf("PrivateKeyToAddress() error = %v", err)
	}
	if addr != w.Address {
		t.Errorf("PrivateKeyToAddress(%q) = %q, want %q", w.PrivateKey, addr, w.Address)
	}
}

func TestPrivateKeyToAddressStripPrefix(t *testing.T) {
	w, _ := Generate()
	noPrefix := strings.TrimPrefix(w.PrivateKey, "0x")

	addr, err := PrivateKeyToAddress(noPrefix)
	if err != nil {
		t.Fatalf("PrivateKeyToAddress without 0x: %v", err)
	}
	if addr != w.Address {
		t.Errorf("got %q, want %q", addr, w.Address)
	}
}

func TestPrivateKeyToAddressInvalid(t *testing.T) {
	_, err := PrivateKeyToAddress("0xnothex")
	if err == nil {
		t.Error("expected error for invalid private key, got nil")
	}
}

func TestPublicKeyToAddress(t *testing.T) {
	w, _ := Generate()
	key, err := crypto.HexToECDSA(strings.TrimPrefix(w.PrivateKey, "0x"))
	if err != nil {
		t.Fatal(err)
	}
	addr := PublicKeyToAddress(&key.PublicKey)
	if addr != w.Address {
		t.Errorf("got %q, want %q", addr, w.Address)
	}
}
