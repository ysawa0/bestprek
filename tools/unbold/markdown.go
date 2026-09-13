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

type markdownProtector struct {
	input       string
	protected   []bool
	fence       byte
	fenceLength int
}

func (p *markdownProtector) protect(start, end int) {
	for i := start; i < end; i++ {
		p.protected[i] = true
	}
}

func lineEnd(input string, start int) int {
	if newline := strings.IndexByte(input[start:], '\n'); newline >= 0 {
		return start + newline + 1
	}
	return len(input)
}

func (p *markdownProtector) updateFence(trimmed string, indented bool) {
	if indented || len(trimmed) == 0 {
		return
	}
	marker := trimmed[0]
	if marker != '`' && marker != '~' {
		return
	}
	length := runLength(trimmed, 0)
	if p.fence == 0 {
		if length >= 3 {
			p.fence, p.fenceLength = marker, length
		}
		return
	}
	if p.fence != marker || length < p.fenceLength {
		return
	}
	if strings.TrimSpace(trimmed[length:]) == "" {
		p.fence, p.fenceLength = 0, 0
	}
}

func (p *markdownProtector) protectLine(start int) (int, bool) {
	end := lineEnd(p.input, start)
	line := p.input[start:end]
	leadingSpaces := len(line) - len(strings.TrimLeft(line, " "))
	indented := leadingSpaces >= 4 || strings.HasPrefix(line[leadingSpaces:], "\t")
	trimmed := strings.TrimLeft(line, " >\t")
	wasFenced := p.fence != 0
	p.updateFence(trimmed, indented)
	if wasFenced || p.fence != 0 || indented {
		return end, true
	}
	return end, thematicBreak(trimmed) || reference.MatchString(line)
}

func inlineProtectionEnd(input string, start int) int {
	if input[start] == '\\' && start+1 < len(input) {
		return start + 2
	}
	if input[start] == '`' {
		return inlineCodeEnd(input, start)
	}
	if input[start] == '<' {
		return htmlEnd(input, start)
	}
	if input[start] == '(' && start > 0 && input[start-1] == ']' {
		return linkEnd(input, start)
	}
	return start
}

// Mark syntax whose literal content must never be rewritten as emphasis.
func protectedMarkdown(input string) []bool {
	protector := markdownProtector{input: input, protected: make([]bool, len(input))}
	for i := 0; i < len(input); {
		if i == 0 || input[i-1] == '\n' {
			if end, protect := protector.protectLine(i); protect {
				protector.protect(i, end)
				i = end
				continue
			}
		}
		end := inlineProtectionEnd(input, i)
		if end > i {
			protector.protect(i, end)
			i = end
		} else {
			i++
		}
	}
	return protector.protected
}
