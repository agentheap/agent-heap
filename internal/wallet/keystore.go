package wallet

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"

	"golang.org/x/crypto/scrypt"
)

// Keystore represents an encrypted private key file.
type Keystore struct {
	Address    string `json:"address"`
	Ciphertext string `json:"ciphertext"`
	Salt       string `json:"salt"`
	Nonce      string `json:"nonce"`
}

// EncryptKey encrypts a hex-encoded private key with a passphrase using
// AES-256-GCM with a scrypt-derived key. Returns JSON bytes.
func EncryptKey(privateKeyHex string, passphrase string) ([]byte, error) {
	// Strip 0x prefix
	key := privateKeyHex
	if strings.HasPrefix(key, "0x") {
		key = key[2:]
	}

	// Derive address
	addr, err := PrivateKeyToAddress(privateKeyHex)
	if err != nil {
		return nil, fmt.Errorf("derive address: %w", err)
	}

	// Generate random salt for scrypt
	salt := make([]byte, 32)
	if _, err := rand.Read(salt); err != nil {
		return nil, fmt.Errorf("generate salt: %w", err)
	}

	// Derive encryption key using scrypt
	encKey, err := scrypt.Key([]byte(passphrase), salt, 1<<17, 8, 1, 32)
	if err != nil {
		return nil, fmt.Errorf("scrypt key derivation: %w", err)
	}

	// Create AES cipher
	block, err := aes.NewCipher(encKey)
	if err != nil {
		return nil, fmt.Errorf("aes cipher: %w", err)
	}

	// Generate random nonce for GCM
	nonce := make([]byte, 12)
	if _, err := rand.Read(nonce); err != nil {
		return nil, fmt.Errorf("generate nonce: %w", err)
	}

	// Encrypt with AES-GCM
	aesGCM, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("gcm: %w", err)
	}

	ciphertext := aesGCM.Seal(nil, nonce, []byte(key), nil)

	ks := Keystore{
		Address:    addr,
		Ciphertext: base64.StdEncoding.EncodeToString(ciphertext),
		Salt:       base64.StdEncoding.EncodeToString(salt),
		Nonce:      base64.StdEncoding.EncodeToString(nonce),
	}

	return json.MarshalIndent(ks, "", "  ")
}

// DecryptKeystore decrypts a JSON keystore and returns the hex private key.
func DecryptKeystore(data []byte, passphrase string) (string, error) {
	var ks Keystore
	if err := json.Unmarshal(data, &ks); err != nil {
		return "", fmt.Errorf("parse keystore: %w", err)
	}

	salt, err := base64.StdEncoding.DecodeString(ks.Salt)
	if err != nil {
		return "", fmt.Errorf("decode salt: %w", err)
	}

	nonce, err := base64.StdEncoding.DecodeString(ks.Nonce)
	if err != nil {
		return "", fmt.Errorf("decode nonce: %w", err)
	}

	ciphertext, err := base64.StdEncoding.DecodeString(ks.Ciphertext)
	if err != nil {
		return "", fmt.Errorf("decode ciphertext: %w", err)
	}

	// Derive key with same parameters
	encKey, err := scrypt.Key([]byte(passphrase), salt, 1<<17, 8, 1, 32)
	if err != nil {
		return "", fmt.Errorf("scrypt key derivation: %w", err)
	}

	// Decrypt
	block, err := aes.NewCipher(encKey)
	if err != nil {
		return "", fmt.Errorf("aes cipher: %w", err)
	}

	aesGCM, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("gcm: %w", err)
	}

	plaintext, err := aesGCM.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return "", fmt.Errorf("decrypt failed (wrong passphrase?): %w", err)
	}

	privateKeyHex := "0x" + string(plaintext)

	// Validate the decrypted key derives the same address
	derivedAddr, err := PrivateKeyToAddress(privateKeyHex)
	if err != nil {
		return "", fmt.Errorf("decrypted key is invalid: %w", err)
	}
	if !strings.EqualFold(derivedAddr, ks.Address) {
		return "", fmt.Errorf("decrypted key does not match stored address (got %s, want %s)", derivedAddr, ks.Address)
	}

	return privateKeyHex, nil
}

// GenerateEncrypted creates a new wallet and immediately encrypts it.
// Returns the encrypted keystore JSON and the address.
func GenerateEncrypted(passphrase string) ([]byte, string, error) {
	w, err := Generate()
	if err != nil {
		return nil, "", fmt.Errorf("generate key: %w", err)
	}

	keystoreJSON, err := EncryptKey(w.PrivateKey, passphrase)
	if err != nil {
		return nil, "", fmt.Errorf("encrypt key: %w", err)
	}

	return keystoreJSON, w.Address, nil
}

// LoadPrivateKey loads a private key from either a keystore file or env var.
// If KEYSTORE_FILE and KEYSTORE_PASSPHRASE are set, uses the keystore.
// Falls back to PRIVATE_KEY env var.
// Returns the hex private key and the address.
func LoadPrivateKey(keystoreFile, keystorePassphrase, fallbackKey string) (string, string, error) {
	if keystoreFile != "" && keystorePassphrase != "" {
		// Read keystore file is done by the caller — we receive the content
		// This function handles the already-read content case
		return "", "", fmt.Errorf("use LoadPrivateKeyFromFile for file-based loading")
	}

	if fallbackKey != "" {
		addr, err := PrivateKeyToAddress(fallbackKey)
		if err != nil {
			return "", "", fmt.Errorf("invalid PRIVATE_KEY: %w", err)
		}
		return fallbackKey, addr, nil
	}

	return "", "", fmt.Errorf("no private key found (set PRIVATE_KEY or KEYSTORE_FILE + KEYSTORE_PASSPHRASE)")
}

// LoadPrivateKeyFromReader reads a key from a keystore JSON byte slice.
func LoadPrivateKeyFromReader(keystoreData []byte, passphrase string) (string, string, error) {
	privateKey, err := DecryptKeystore(keystoreData, passphrase)
	if err != nil {
		return "", "", fmt.Errorf("decrypt keystore: %w", err)
	}

	addr, err := PrivateKeyToAddress(privateKey)
	if err != nil {
		return "", "", fmt.Errorf("derive address: %w", err)
	}

	return privateKey, addr, nil
}

// Validate that crypto is used (satisfies import)
