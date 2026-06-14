// Package event parses raw log lines into structured service request events.
package event

import (
	"strconv"
	"strings"
)

// Event is one parsed service request record.
type Event struct {
	Timestamp string
	Service   string
	LatencyMS int
	Status    int
}

// ParseLine parses one CSV line of the form
//
//	timestamp,service,latency_ms,status
//
// It returns ok=false for malformed lines (wrong field count, empty service, or
// a non-integer latency/status) so the caller can skip and count them instead of
// failing hard.
func ParseLine(line string) (Event, bool) {
	fields := strings.Split(line, ",")
	if len(fields) != 4 {
		return Event{}, false
	}

	service := strings.TrimSpace(fields[1])
	if service == "" {
		return Event{}, false
	}

	latency, err := strconv.Atoi(strings.TrimSpace(fields[2]))
	if err != nil {
		return Event{}, false
	}

	status, err := strconv.Atoi(strings.TrimSpace(fields[3]))
	if err != nil {
		return Event{}, false
	}

	return Event{
		Timestamp: strings.TrimSpace(fields[0]),
		Service:   service,
		LatencyMS: latency,
		Status:    status,
	}, true
}
