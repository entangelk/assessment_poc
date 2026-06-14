package rollup

import "testing"

import "pulse/internal/event"

func TestAggregate(t *testing.T) {
	events := []event.Event{
		{Service: "checkout", LatencyMS: 42, Status: 200},
		{Service: "checkout", LatencyMS: 510, Status: 500},
		{Service: "search", LatencyMS: 18, Status: 200},
		{Service: "search", LatencyMS: 27, Status: 200},
	}

	got := Aggregate(events)
	if len(got) != 2 {
		t.Fatalf("expected 2 services, got %d", len(got))
	}

	// Sorted by service name: checkout, then search.
	checkout := got[0]
	if checkout.Service != "checkout" {
		t.Fatalf("expected checkout first (sorted), got %q", checkout.Service)
	}
	if checkout.Count != 2 {
		t.Errorf("checkout count: want 2, got %d", checkout.Count)
	}
	if checkout.ErrorRate != 0.5 {
		t.Errorf("checkout error rate: want 0.5, got %v", checkout.ErrorRate)
	}
	if checkout.P95Latency != 510 {
		t.Errorf("checkout p95: want 510, got %d", checkout.P95Latency)
	}

	search := got[1]
	if search.ErrorRate != 0.0 {
		t.Errorf("search error rate: want 0, got %v", search.ErrorRate)
	}
}

func TestPercentileNearestRank(t *testing.T) {
	values := []int{10, 20, 30, 40, 50, 60, 70, 80, 90, 100}
	if got := percentile(values, 95); got != 100 {
		t.Errorf("p95 of 1..100 by tens: want 100, got %d", got)
	}
	if got := percentile([]int{}, 95); got != 0 {
		t.Errorf("p95 of empty: want 0, got %d", got)
	}
}
