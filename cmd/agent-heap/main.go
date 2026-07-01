package main

import (
	"os"

	"github.com/heapchain/agent-heap/internal/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		os.Exit(1)
	}
}
