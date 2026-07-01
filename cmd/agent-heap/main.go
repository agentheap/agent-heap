package main

import (
	"os"

	"github.com/agentheap/agent-heap/internal/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		os.Exit(1)
	}
}
