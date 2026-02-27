package main

import "testing"

func TestFormatMarkdown(t *testing.T) {
	input := "##Heading   \r\n\r\n\r\n*   item one   \n+ item two\n\r\nText   \n"
	want := "## Heading\n\n- item one\n- item two\n\nText\n"

	got := formatMarkdown(input)
	if got != want {
		t.Fatalf("unexpected output\nwant:\n%q\ngot:\n%q", want, got)
	}
}

func TestFormatMarkdownCodeFence(t *testing.T) {
	input := "```py\n##Heading   \n*   item\n```\n\n\n#Title\n"
	want := "```py\n##Heading\n*   item\n```\n\n# Title\n"

	got := formatMarkdown(input)
	if got != want {
		t.Fatalf("unexpected output\nwant:\n%q\ngot:\n%q", want, got)
	}
}

func TestFormatMarkdownStripsTrailingHeadingHashes(t *testing.T) {
	input := "### title ###   \n"
	want := "### title\n"

	got := formatMarkdown(input)
	if got != want {
		t.Fatalf("unexpected output\nwant:\n%q\ngot:\n%q", want, got)
	}
}
