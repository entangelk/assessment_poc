// Command pulse reads service request events and prints a per-service metrics
// summary as a text table or JSON.
//
// Usage:
//
//	pulse [--json] [FILE]
//
// With no FILE, events are read from standard input. Malformed lines are skipped
// and counted on standard error.
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"pulse/internal/event"
	"pulse/internal/rollup"
)

func main() {
	if err := run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, "pulse:", err)
		os.Exit(1)
	}
}

func run(args []string, stdin io.Reader, stdout, stderr io.Writer) error {
	asJSON := false
	path := ""
	for _, a := range args {
		switch {
		case a == "--json":
			asJSON = true
		case strings.HasPrefix(a, "-"):
			return fmt.Errorf("unknown flag %q", a)
		default:
			path = a
		}
	}

	var input io.Reader = stdin
	if path != "" {
		f, err := os.Open(path)
		if err != nil {
			return err
		}
		defer f.Close()
		input = f
	}

	events, skipped := readEvents(input)
	summaries := rollup.Aggregate(events)

	if skipped > 0 {
		fmt.Fprintf(stderr, "skipped %d malformed line(s)\n", skipped)
	}

	if asJSON {
		enc := json.NewEncoder(stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(summaries)
	}
	return writeTable(stdout, summaries)
}

func readEvents(r io.Reader) ([]event.Event, int) {
	var events []event.Event
	skipped := 0

	scanner := bufio.NewScanner(r)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		e, ok := event.ParseLine(line)
		if !ok {
			skipped++
			continue
		}
		events = append(events, e)
	}
	return events, skipped
}

func writeTable(w io.Writer, summaries []rollup.ServiceSummary) error {
	if _, err := fmt.Fprintf(w, "%-12s %6s %10s %8s\n", "SERVICE", "COUNT", "ERROR_RATE", "P95_MS"); err != nil {
		return err
	}
	for _, s := range summaries {
		if _, err := fmt.Fprintf(w, "%-12s %6d %10.2f %8d\n", s.Service, s.Count, s.ErrorRate, s.P95Latency); err != nil {
			return err
		}
	}
	return nil
}
