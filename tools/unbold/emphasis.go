package main

import (
	"strings"
	"unicode"
	"unicode/utf8"
)

type delimiter struct {
	start, length int
	marker        byte
	canOpen       bool
	canClose      bool
}

func surrounding(text string, start, end int) (rune, rune) {
	before, after := ' ', ' '
	if start > 0 {
		before, _ = utf8.DecodeLastRuneInString(text[:start])
	}
	if end < len(text) {
		after, _ = utf8.DecodeRuneInString(text[end:])
	}
	return before, after
}

func punctuation(char rune) bool {
	return unicode.IsPunct(char) || unicode.IsSymbol(char)
}

func newDelimiter(text string, start, length int) delimiter {
	before, after := surrounding(text, start, start+length)
	left := !unicode.IsSpace(after) && (!punctuation(after) || unicode.IsSpace(before) || punctuation(before))
	right := !unicode.IsSpace(before) && (!punctuation(before) || unicode.IsSpace(after) || punctuation(after))
	if text[start] == '_' {
		return delimiter{start, length, '_', left && (!right || punctuation(before)), right && (!left || punctuation(after))}
	}
	return delimiter{start, length, '*', left, right}
}

func matchDelimiter(open, close delimiter) bool {
	if !open.canOpen || open.marker != close.marker {
		return false
	}
	// The rule of three prevents ambiguous runs from pairing across emphasis.
	return !(open.canClose || close.canOpen) || (open.length+close.length)%3 != 0 || (open.length%3 == 0 && close.length%3 == 0)
}

func consumeDelimiter(stack []delimiter, close delimiter, removed []bool) ([]delimiter, delimiter) {
	for close.canClose && close.length > 0 {
		index := len(stack) - 1
		for index >= 0 && !matchDelimiter(stack[index], close) {
			index--
		}
		if index < 0 {
			break
		}
		open := &stack[index]
		count := 1
		if open.length >= 2 && close.length >= 2 {
			count = 2
			for offset := 0; offset < count; offset++ {
				removed[open.start+open.length-count+offset] = true
				removed[close.start+offset] = true
			}
		}
		open.length -= count
		close.start += count
		close.length -= count
		stack = stack[:index+1]
		if open.length == 0 {
			stack = stack[:index]
		}
	}
	return stack, close
}

// Remove paired strong-emphasis delimiters, leaving single emphasis intact.
func stripBold(input string) string {
	protected := protectedMarkdown(input)
	removed := make([]bool, len(input))
	var stack []delimiter
	for i := 0; i < len(input); {
		if i == 0 || input[i-1] == '\n' {
			line, _, _ := strings.Cut(input[i:], "\n")
			if strings.Trim(line, " \t\r") == "" {
				stack = nil
			}
		}
		if protected[i] || (input[i] != '*' && input[i] != '_') {
			i++
			continue
		}
		length := runLength(input, i)
		current := newDelimiter(input, i, length)
		stack, current = consumeDelimiter(stack, current, removed)
		if current.canOpen && current.length > 0 {
			stack = append(stack, current)
		}
		i += length
	}
	var out strings.Builder
	for i := range len(input) {
		if !removed[i] {
			out.WriteByte(input[i])
		}
	}
	return out.String()
}
