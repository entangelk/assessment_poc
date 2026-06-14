// Package rollup aggregates parsed events into per-service summaries.
package rollup

import (
	"sort"

	"pulse/internal/event"
)

// ServiceSummary holds the aggregated metrics for one service.
type ServiceSummary struct {
	Service    string  `json:"service"`
	Count      int     `json:"count"`
	ErrorRate  float64 `json:"error_rate"`
	P95Latency int     `json:"p95_latency_ms"`
}

// Aggregate computes per-service summaries, sorted by service name.
//
// A request counts as an error when its status is 500 or above. The p95 latency
// uses the nearest-rank method (see docs/design.md).
func Aggregate(events []event.Event) []ServiceSummary {
	byService := map[string][]event.Event{}
	for _, e := range events {
		byService[e.Service] = append(byService[e.Service], e)
	}

	summaries := make([]ServiceSummary, 0, len(byService))
	for service, evs := range byService {
		errors := 0
		latencies := make([]int, 0, len(evs))
		for _, e := range evs {
			if e.Status >= 500 {
				errors++
			}
			latencies = append(latencies, e.LatencyMS)
		}
		summaries = append(summaries, ServiceSummary{
			Service:    service,
			Count:      len(evs),
			ErrorRate:  float64(errors) / float64(len(evs)),
			P95Latency: percentile(latencies, 95),
		})
	}

	sort.Slice(summaries, func(i, j int) bool {
		return summaries[i].Service < summaries[j].Service
	})
	return summaries
}

// percentile returns the nearest-rank percentile of the values.
//
// rank = ceil(p/100 * n), 1-indexed and clamped into range.
func percentile(values []int, p int) int {
	if len(values) == 0 {
		return 0
	}
	sorted := append([]int(nil), values...)
	sort.Ints(sorted)

	rank := (p*len(sorted) + 99) / 100 // ceil division
	if rank < 1 {
		rank = 1
	}
	if rank > len(sorted) {
		rank = len(sorted)
	}
	return sorted[rank-1]
}
