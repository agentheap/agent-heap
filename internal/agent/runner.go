package agent

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
)

// Result represents the output of a single agent graph run.
type Result map[string]interface{}

// Run executes the Python agent graph as a subprocess.
// It calls `python3 -m agent.graph` and returns the parsed JSON result.
func Run() (Result, error) {
	cmd := exec.Command("python3", "-m", "agent.graph")

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

// RunWithEnv executes the Python agent graph with additional environment variables.
func RunWithEnv(extraEnv map[string]string) (Result, error) {
	cmd := exec.Command("python3", "-m", "agent.graph")

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
