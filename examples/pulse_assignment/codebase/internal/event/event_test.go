package event

import "testing"

func TestParseLineValid(t *testing.T) {
	e, ok := ParseLine("2026-03-01T10:00:01Z,checkout,510,500")
	if !ok {
		t.Fatal("expected valid line to parse")
	}
	if e.Service != "checkout" || e.LatencyMS != 510 || e.Status != 500 {
		t.Fatalf("unexpected parse result: %+v", e)
	}
}

func TestParseLineMalformed(t *testing.T) {
	cases := map[string]string{
		"too few fields":   "2026-03-01T10:00:01Z,checkout,510",
		"too many fields":  "2026-03-01T10:00:01Z,checkout,510,500,extra",
		"empty service":    "2026-03-01T10:00:02Z,,,",
		"latency not int":  "2026-03-01T10:00:01Z,checkout,fast,200",
		"status not int":   "2026-03-01T10:00:01Z,checkout,510,oops",
	}
	for name, line := range cases {
		if _, ok := ParseLine(line); ok {
			t.Errorf("%s: expected malformed, but parsed", name)
		}
	}
}
