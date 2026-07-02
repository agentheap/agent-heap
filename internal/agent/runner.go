package agent

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/agentheap/agent-heap/internal/wallet"
)

// execCommand is overridable in tests to avoid running real python3.
var execCommand = exec.Command

// Result represents the output of a single agent graph run.
type Result map[string]interface{}

// pythonCmd returns the command to run the agent graph.
func pythonCmd() (string, []string) {
	if _, err := exec.LookPath("uv"); err == nil {
		cwd, _ := os.Getwd()
		if cwd != "" {
			if _, err := os.Stat(filepath.Join(cwd, "pyproject.toml")); err == nil {
				return "uv", []string{"run", "python3", "-m", "agent.graph"}
			}
		}
	}

	cwd, _ := os.Getwd()
	if cwd != "" {
		venvPython := filepath.Join(cwd, ".venv", "bin", "python3")
		if _, err := os.Stat(venvPython); err == nil {
			return venvPython, []string{"-m", "agent.graph"}
		}
	}

	return "python3", []string{"-m", "agent.graph"}
}

// ResolvePrivateKey loads the private key from the configured source.
// Priority: KEYSTORE_FILE + KEYSTORE_PASSPHRASE > PRIVATE_KEY env var.
// Returns the hex private key (with 0x prefix), the derived address, or an error.
func ResolvePrivateKey() (string, string, error) {
	ksFile := os.Getenv("KEYSTORE_FILE")
	ksPass := os.Getenv("KEYSTORE_PASSPHRASE")

	if ksFile != "" && ksPass != "" {
		data, err := os.ReadFile(ksFile)
		if err != nil {
			return "", "", fmt.Errorf("read keystore %s: %w", ksFile, err)
		}
		privateKey, addr, err := wallet.LoadPrivateKeyFromReader(data, ksPass)
		if err != nil {
			return "", "", fmt.Errorf("decrypt keystore: %w", err)
		}
		return privateKey, addr, nil
	}

	pk := os.Getenv("PRIVATE_KEY")
	if pk != "" {
		addr, err := wallet.PrivateKeyToAddress(pk)
		if err != nil {
			return "", "", fmt.Errorf("invalid PRIVATE_KEY: %w", err)
		}
		return pk, addr, nil
	}

	return "", "", fmt.Errorf("no private key configured (set KEYSTORE_FILE + KEYSTORE_PASSPHRASE, or PRIVATE_KEY)")
}

// Run executes the Python agent graph as a subprocess.
func Run() (Result, error) {
	cmdName, cmdArgs := pythonCmd()
	cmd := execCommand(cmdName, cmdArgs...)

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("agent graph exited (%v): %s", exitErr, string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("run agent graph: %w", err)
	}

	outStr := strings.TrimSpace(string(output))
	if outStr == "" {
		return Result{}, nil
	}

	var result Result
	if err := json.Unmarshal([]byte(outStr), &result); err != nil {
		return nil, fmt.Errorf("parse agent output: %w", err)
	}

	return result, nil
}

// RunWithKey loads the private key from the configured source and passes it
// to the Python subprocess as PRIVATE_KEY. Falls back to plain Run() if
// no key is configured.
func RunWithKey() (Result, string, error) {
	privateKey, addr, err := ResolvePrivateKey()
	if err != nil {
		// No key configured — run without it (simulated mode)
		result, runErr := Run()
		return result, "", runErr
	}

	cmdName, cmdArgs := pythonCmd()
	cmd := execCommand(cmdName, cmdArgs...)

	// Set PRIVATE_KEY in subprocess environment
	cmd.Env = append(cmd.Environ(), fmt.Sprintf("PRIVATE_KEY=%s", privateKey))

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, addr, fmt.Errorf("agent graph exited (%v): %s", exitErr, string(exitErr.Stderr))
		}
		return nil, addr, fmt.Errorf("run agent graph: %w", err)
	}

	outStr := strings.TrimSpace(string(output))
	if outStr == "" {
		return Result{}, addr, nil
	}

	var result Result
	if err := json.Unmarshal([]byte(outStr), &result); err != nil {
		return nil, addr, fmt.Errorf("parse agent output: %w", err)
	}

	return result, addr, nil
}

// RunWithEnv executes the Python agent graph with additional environment variables.
func RunWithEnv(extraEnv map[string]string) (Result, error) {
	cmdName, cmdArgs := pythonCmd()
	cmd := execCommand(cmdName, cmdArgs...)

	for k, v := range extraEnv {
		cmd.Env = append(cmd.Environ(), fmt.Sprintf("%s=%s", k, v))
	}

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("agent graph exited (%v): %s", exitErr, string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("run agent graph: %w", err)
	}

	outStr := strings.TrimSpace(string(output))
	if outStr == "" {
		return Result{}, nil
	}

	var result Result
	if err := json.Unmarshal([]byte(outStr), &result); err != nil {
		return nil, fmt.Errorf("parse agent output: %w", err)
	}

	return result, nil
}
