package main

import "strings"

func runLength(text string, start int) int {
	end := start
	for end < len(text) && text[end] == text[start] {
		end++
	}
	return end - start
}

// Keep code and escaped punctuation byte-for-byte while stripping prose markers.
func stripBold(input string) string {
	var out strings.Builder
	var fence byte
	fenceLength := 0
	for i := 0; i < len(input); {
		if i == 0 || input[i-1] == '\n' {
			end := strings.IndexByte(input[i:], '\n')
			if end < 0 {
				end = len(input)
			} else {
				end += i + 1
			}
			line := input[i:end]
			trimmed := strings.TrimLeft(line, " >\t")
			if len(trimmed) > 0 && (trimmed[0] == '`' || trimmed[0] == '~') {
				n := runLength(trimmed, 0)
				if fence == 0 && n >= 3 {
					fence, fenceLength = trimmed[0], n
					out.WriteString(line)
					i = end
					continue
				}
				if fence == trimmed[0] && n >= fenceLength && strings.TrimSpace(trimmed[n:]) == "" {
					fence = 0
					out.WriteString(line)
					i = end
					continue
				}
			}
			if fence != 0 || strings.HasPrefix(line, "    ") || strings.HasPrefix(line, "\t") {
				out.WriteString(line)
				i = end
				continue
			}
		}
		if input[i] == '\\' && i+1 < len(input) {
			out.WriteString(input[i : i+2])
			i += 2
			continue
		}
		if input[i] == '`' {
			n := runLength(input, i)
			end := i + n
			for end < len(input) {
				if input[end] != '`' {
					end++
					continue
				}
				closing := runLength(input, end)
				end += closing
				if closing == n {
					break
				}
			}
			out.WriteString(input[i:end])
			i = end
			continue
		}
		if strings.HasPrefix(input[i:], "**") || strings.HasPrefix(input[i:], "__") {
			i += 2
			continue
		}
		out.WriteByte(input[i])
		i++
	}
	return out.String()
}
