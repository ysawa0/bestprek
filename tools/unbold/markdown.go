package main

import (
	"regexp"
	"strings"
)

var (
	rawCode   = regexp.MustCompile(`(?is)^<(code|pre|script|style)\b[^>]*>`)
	reference = regexp.MustCompile(`^ {0,3}\[[^\]]+\]:`)
)

func runLength(text string, start int) int {
	end := start
	for end < len(text) && text[end] == text[start] {
		end++
	}
	return end - start
}

func thematicBreak(line string) bool {
	compact := strings.Map(func(char rune) rune {
		if char == ' ' || char == '\t' || char == '\r' || char == '\n' {
			return -1
		}
		return char
	}, line)
	return len(compact) >= 3 && (compact[0] == '*' || compact[0] == '_') && runLength(compact, 0) == len(compact)
}

func inlineCodeEnd(text string, start int) int {
	length := runLength(text, start)
	for cursor := start + length; cursor < len(text); {
		if text[cursor] != '`' {
			cursor++
			continue
		}
		closing := runLength(text, cursor)
		cursor += closing
		if closing == length {
			return cursor
		}
	}
	return start + length
}

func linkEnd(text string, start int) int {
	depth := 1
	var quote byte
	for cursor := start + 1; cursor < len(text); cursor++ {
		char := text[cursor]
		if char == '\\' {
			cursor++
			continue
		}
		if quote != 0 {
			if char == quote {
				quote = 0
			}
			continue
		}
		if char == '"' || char == '\'' {
			quote = char
		} else if char == '(' {
			depth++
		} else if char == ')' {
			depth--
			if depth == 0 {
				return cursor + 1
			}
		}
	}
	return start
}

func htmlEnd(text string, start int) int {
	remaining := text[start:]
	if strings.HasPrefix(remaining, "<!--") {
		if end := strings.Index(remaining, "-->"); end >= 0 {
			return start + end + 3
		}
		return len(text)
	}
	if match := rawCode.FindStringSubmatch(remaining); match != nil {
		closing := "</" + strings.ToLower(match[1]) + ">"
		if end := strings.Index(strings.ToLower(remaining), closing); end >= 0 {
			return start + end + len(closing)
		}
		return len(text)
	}
	var quote byte
	for cursor := start + 1; cursor < len(text); cursor++ {
		char := text[cursor]
		if quote != 0 {
			if char == quote {
				quote = 0
			}
		} else if char == '\'' || char == '"' {
			quote = char
		} else if char == '>' {
			return cursor + 1
		} else if char == '\n' {
			return start
		}
	}
	return start
}

// Mark syntax whose literal content must never be rewritten as emphasis.
func protectedMarkdown(input string) []bool {
	protected := make([]bool, len(input))
	protect := func(start, end int) {
		for i := start; i < end; i++ {
			protected[i] = true
		}
	}
	var fence byte
	fenceLength := 0
	for i := 0; i < len(input); {
		if i == 0 || input[i-1] == '\n' {
			end := len(input)
			if newline := strings.IndexByte(input[i:], '\n'); newline >= 0 {
				end = i + newline + 1
			}
			line := input[i:end]
			leadingSpaces := len(line) - len(strings.TrimLeft(line, " "))
			indented := leadingSpaces >= 4 || strings.HasPrefix(line[leadingSpaces:], "\t")
			trimmed := strings.TrimLeft(line, " >\t")
			wasFenced := fence != 0
			if !indented && len(trimmed) > 0 && (trimmed[0] == '`' || trimmed[0] == '~') {
				n := runLength(trimmed, 0)
				if fence == 0 && n >= 3 {
					fence, fenceLength = trimmed[0], n
				} else if fence == trimmed[0] && n >= fenceLength && strings.TrimSpace(trimmed[n:]) == "" {
					fence = 0
				}
			}
			if wasFenced || fence != 0 || indented || thematicBreak(trimmed) || reference.MatchString(line) {
				protect(i, end)
				i = end
				continue
			}
		}
		end := i
		switch {
		case input[i] == '\\' && i+1 < len(input):
			end = i + 2
		case input[i] == '`':
			end = inlineCodeEnd(input, i)
		case input[i] == '<':
			end = htmlEnd(input, i)
		case input[i] == '(' && i > 0 && input[i-1] == ']':
			end = linkEnd(input, i)
		}
		if end > i {
			protect(i, end)
			i = end
		} else {
			i++
		}
	}
	return protected
}
