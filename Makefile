BINARY ?= agent-heap
GOOS   ?= linux
GOARCH ?= amd64

.PHONY: build clean test run

build:
	CGO_ENABLED=0 GOOS=$(GOOS) GOARCH=$(GOARCH) go build \
		-ldflags="-s -w" \
		-o $(BINARY) \
		./cmd/agent-heap/

clean:
	rm -f $(BINARY)
	rm -f agent-heap.db

test:
	go test ./...

run: build
	./$(BINARY)
