package agent

import (
	"encoding/json"
	"os"
	"os/exec"
	"testing"
)

func TestRunExecutableNotFound(t *testing.T) {
	// Save and restore PATH
	oldPath := os.Getenv("PATH")
	defer os.Setenv("PATH", oldPath)
	os.Setenv("PATH", "/nonexistent")

	// Override exec.Command for this test
	execCommand = func(name string, arg ...string) *exec.Cmd {
		cmd := exec.Command("/nonexistent/python3", "-m", "agent.graph")
		return cmd
	}
	defer func() { execCommand = exec.Command }()

	_, err := Run()
	if err == nil {
		t.Error("expected error when python3 not found, got nil")
	}
}

func TestRunParsesJSON(t *testing.T) {
	execCommand = func(name string, arg ...string) *exec.Cmd {
		cmd := exec.Command("echo", `{"tx_result":{"action":"deposit","protocol":"aave","pool":"USDC","amount":1.0},"analysis":{"protocol":"aave","apy":5.2}}`)
		return cmd
	}
	defer func() { execCommand = exec.Command }()

	result, err := Run()
	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}

	tx, ok := result["tx_result"].(map[string]interface{})
	if !ok {
		t.Fatal("expected tx_result in result")
	}
	if tx["action"] != "deposit" {
		t.Errorf("action = %v, want deposit", tx["action"])
	}
	if tx["protocol"] != "aave" {
		t.Errorf("protocol = %v, want aave", tx["protocol"])
	}
	if tx["amount"] != 1.0 {
		t.Errorf("amount = %v, want 1.0", tx["amount"])
	}
}

func TestRunHandlesEmptyOutput(t *testing.T) {
	execCommand = func(name string, arg ...string) *exec.Cmd {
		return exec.Command("echo", "")
	}
	defer func() { execCommand = exec.Command }()

	result, err := Run()
	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}
	if result == nil {
		t.Error("expected non-nil result")
	}
}

func TestRunHandlesInvalidJSON(t *testing.T) {
	execCommand = func(name string, arg ...string) *exec.Cmd {
		return exec.Command("echo", "not json at all")
	}
	defer func() { execCommand = exec.Command }()

	_, err := Run()
	if err == nil {
		t.Error("expected error for invalid JSON, got nil")
	}
}

func TestRunWithEnv(t *testing.T) {
	execCommand = func(name string, arg ...string) *exec.Cmd {
		cmd := exec.Command("echo", `{"tx_result":{"action":"deposit"}}`)
		cmd.Env = append(cmd.Environ(), "CUSTOM_VAR=test")
		return cmd
	}
	defer func() { execCommand = exec.Command }()

	result, err := RunWithEnv(map[string]string{"CUSTOM_VAR": "test"})
	if err != nil {
		t.Fatalf("RunWithEnv() error = %v", err)
	}

	tx, ok := result["tx_result"].(map[string]interface{})
	if !ok {
		t.Fatal("expected tx_result in result")
	}
	if tx["action"] != "deposit" {
		t.Errorf("action = %v, want deposit", tx["action"])
	}
}

func TestResultIsMap(t *testing.T) {
	var r Result
	data := []byte(`{"key":"value","nested":{"a":1}}`)
	if err := json.Unmarshal(data, &r); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if r["key"] != "value" {
		t.Errorf("key = %v, want value", r["key"])
	}
	nested, ok := r["nested"].(map[string]interface{})
	if !ok {
		t.Fatal("expected nested to be map")
	}
	if nested["a"] != float64(1) {
		t.Errorf("nested.a = %v, want 1", nested["a"])
	}
}
