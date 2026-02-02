package main

import "testing"

func TestStripBold(t *testing.T) {
	input := "**bold** and __strong__"
	got := stripBold(input)
	want := "bold and strong"
	if got != want {
		t.Fatalf("expected %q, got %q", want, got)
	}
}
