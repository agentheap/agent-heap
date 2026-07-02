package wallet

import (
	"strings"
	"testing"
)

func TestEncryptAndDecrypt(t *testing.T) {
	w, err := Generate()
	if err != nil {
		t.Fatal(err)
	}

	passphrase := "test-passphrase-123!@#"

	encrypted, err := EncryptKey(w.PrivateKey, passphrase)
	if err != nil {
		t.Fatalf("EncryptKey() error = %v", err)
	}
	if len(encrypted) == 0 {
		t.Fatal("EncryptKey() returned empty data")
	}

	decrypted, err := DecryptKeystore(encrypted, passphrase)
	if err != nil {
		t.Fatalf("DecryptKeystore() error = %v", err)
	}
	if !strings.EqualFold(decrypted, w.PrivateKey) {
		t.Errorf("decrypted key = %q, want %q", decrypted, w.PrivateKey)
	}
}

func TestDecryptWrongPassphrase(t *testing.T) {
	w, err := Generate()
	if err != nil {
		t.Fatal(err)
	}

	encrypted, err := EncryptKey(w.PrivateKey, "correct-passphrase")
	if err != nil {
		t.Fatal(err)
	}

	_, err = DecryptKeystore(encrypted, "wrong-passphrase")
	if err == nil {
		t.Error("expected error for wrong passphrase, got nil")
	}
}

func TestDecryptInvalidData(t *testing.T) {
	_, err := DecryptKeystore([]byte("not-json"), "pass")
	if err == nil {
		t.Error("expected error for invalid JSON, got nil")
	}
}

func TestGenerateEncrypted(t *testing.T) {
	keystoreJSON, addr, err := GenerateEncrypted("test-pass")
	if err != nil {
		t.Fatalf("GenerateEncrypted() error = %v", err)
	}
	if addr == "" {
		t.Error("expected non-empty address")
	}
	if len(keystoreJSON) == 0 {
		t.Fatal("expected non-empty keystore JSON")
	}

	_, err = DecryptKeystore(keystoreJSON, "test-pass")
	if err != nil {
		t.Fatalf("failed to decrypt generated keystore: %v", err)
	}
}

func TestEncryptKeyPreservesAddress(t *testing.T) {
	w, _ := Generate()
	passphrase := "secure-pass"

	encrypted, err := EncryptKey(w.PrivateKey, passphrase)
	if err != nil {
		t.Fatal(err)
	}

	decrypted, err := DecryptKeystore(encrypted, passphrase)
	if err != nil {
		t.Fatal(err)
	}

	addr1, _ := PrivateKeyToAddress(w.PrivateKey)
	addr2, _ := PrivateKeyToAddress(decrypted)
	if !strings.EqualFold(addr1, addr2) {
		t.Errorf("address mismatch: %s vs %s", addr1, addr2)
	}
}

func TestLoadPrivateKeyFromReader(t *testing.T) {
	w, _ := Generate()
	passphrase := "test-reader-pass"

	encrypted, err := EncryptKey(w.PrivateKey, passphrase)
	if err != nil {
		t.Fatal(err)
	}

	privateKey, addr, err := LoadPrivateKeyFromReader(encrypted, passphrase)
	if err != nil {
		t.Fatalf("LoadPrivateKeyFromReader() error = %v", err)
	}
	if !strings.EqualFold(privateKey, w.PrivateKey) {
		t.Errorf("private key mismatch")
	}
	expectedAddr, _ := PrivateKeyToAddress(w.PrivateKey)
	if !strings.EqualFold(addr, expectedAddr) {
		t.Errorf("address mismatch: %s vs %s", addr, expectedAddr)
	}
}

func TestLoadPrivateKeyFromReaderWrongPassphrase(t *testing.T) {
	w, _ := Generate()
	encrypted, _ := EncryptKey(w.PrivateKey, "correct")

	_, _, err := LoadPrivateKeyFromReader(encrypted, "wrong")
	if err == nil {
		t.Error("expected error for wrong passphrase")
	}
}

func TestKeystoreJSONStructure(t *testing.T) {
	w, _ := Generate()

	encrypted, err := EncryptKey(w.PrivateKey, "test")
	if err != nil {
		t.Fatal(err)
	}

	data := string(encrypted)
	if !strings.Contains(data, `"address"`) {
		t.Error("keystore missing address field")
	}
	if !strings.Contains(data, `"ciphertext"`) {
		t.Error("keystore missing ciphertext field")
	}
	if !strings.Contains(data, `"salt"`) {
		t.Error("keystore missing salt field")
	}
	if !strings.Contains(data, `"nonce"`) {
		t.Error("keystore missing nonce field")
	}
}
