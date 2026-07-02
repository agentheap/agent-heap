package agent

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// execCommand is overridable in tests to avoid running real python3.
var execCommand = exec.Command

// Result represents the output of a single agent graph run.
type Result map[string]interface{}

// pythonCmd returns the command to run the agent graph.
// Prefers uv run for venv management, falls back to python3.
func pythonCmd() (string, []string) {
	// Check if uv is available
	if _, err := exec.LookPath("uv"); err == nil {
		// Check if there's a pyproject.toml in cwd
		cwd, _ := os.Getwd()
		if cwd != "" {
			if _, err := os.Stat(filepath.Join(cwd, "pyproject.toml")); err == nil {
				return "uv", []string{"run", "python3", "-m", "agent.graph"}
			}
		}
	}

	// Check .venv/bin/python in cwd
	cwd, _ := os.Getwd()
	if cwd != "" {
		venvPython := filepath.Join(cwd, ".venv", "bin", "python3")
		if _, err := os.Stat(venvPython); err == nil {
			return venvPython, []string{"-m", "agent.graph"}
		}
	}

	return "python3", []string{"-m", "agent.graph"}
}

// Run executes the Python agent graph as a subprocess.
// It calls `python3 -m agent.graph` and returns the parsed JSON result.
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
