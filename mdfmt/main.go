package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
)

var trailingHeadingHashes = regexp.MustCompile(`\s+#+\s*$`)

type fenceState struct {
	active bool
	marker byte
	length int
}

func parseFence(line string) (byte, int, bool) {
	if line == "" {
		return 0, 0, false
	}
	marker := line[0]
	if marker != '`' && marker != '~' {
		return 0, 0, false
	}
	count := 0
	for count < len(line) && line[count] == marker {
		count++
	}
	if count < 3 {
		return 0, 0, false
	}
	return marker, count, true
}

func normalizeHeading(line string) string {
	indentLen := 0
	for indentLen < len(line) && line[indentLen] == ' ' {
		indentLen++
	}
	hashStart := indentLen
	hashEnd := hashStart
	for hashEnd < len(line) && line[hashEnd] == '#' {
		hashEnd++
	}
	hashCount := hashEnd - hashStart
	if hashCount == 0 || hashCount > 6 {
		return line
	}

	content := strings.TrimSpace(line[hashEnd:])
	content = trailingHeadingHashes.ReplaceAllString(content, "")
	content = strings.TrimSpace(content)

	prefix := line[:indentLen] + strings.Repeat("#", hashCount)
	if content == "" {
		return prefix
	}
	return prefix + " " + content
}

func normalizeUnorderedList(line string) string {
	indentLen := 0
	for indentLen < len(line) && line[indentLen] == ' ' {
		indentLen++
	}
	if indentLen >= len(line) {
		return line
	}

	marker := line[indentLen]
	if marker != '-' && marker != '*' && marker != '+' {
		return line
	}
	if indentLen+1 >= len(line) {
		return line
	}
	if line[indentLen+1] != ' ' && line[indentLen+1] != '\t' {
		return line
	}

	content := strings.TrimLeft(line[indentLen+1:], " \t")
	if content == "" {
		return strings.Repeat(" ", indentLen) + "-"
	}
	return strings.Repeat(" ", indentLen) + "- " + content
}

func formatMarkdown(input string) string {
	normalized := strings.ReplaceAll(input, "\r\n", "\n")
	normalized = strings.ReplaceAll(normalized, "\r", "\n")

	lines := strings.Split(normalized, "\n")
	out := make([]string, 0, len(lines))
	blankRun := 0
	fence := fenceState{}

	for _, raw := range lines {
		line := strings.TrimRight(raw, " \t")
		trimmedLeft := strings.TrimLeft(line, " ")

		if marker, count, ok := parseFence(trimmedLeft); ok {
			if !fence.active {
				fence.active = true
				fence.marker = marker
				fence.length = count
			} else if marker == fence.marker && count >= fence.length {
				fence.active = false
			}
			out = append(out, line)
			blankRun = 0
			continue
		}

		if !fence.active {
			line = normalizeHeading(line)
			line = normalizeUnorderedList(line)
		}

		if strings.TrimSpace(line) == "" {
			blankRun++
			if blankRun > 1 {
				continue
			}
			out = append(out, "")
			continue
		}

		blankRun = 0
		out = append(out, line)
	}

	return strings.TrimRight(strings.Join(out, "\n"), "\n") + "\n"
}

func processReader(reader io.Reader, writer io.Writer) error {
	data, err := io.ReadAll(reader)
	if err != nil {
		return err
	}
	_, err = io.WriteString(writer, formatMarkdown(string(data)))
	return err
}

func main() {
	writeInPlace := flag.Bool("write", false, "rewrite files in place")
	flag.Parse()
	paths := flag.Args()

	if len(paths) == 0 {
		if err := processReader(os.Stdin, os.Stdout); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return
	}

	for i, path := range paths {
		data, err := os.ReadFile(path)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}

		out := formatMarkdown(string(data))
		if *writeInPlace {
			info, err := os.Stat(path)
			if err != nil {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			if err := os.WriteFile(path, []byte(out), info.Mode().Perm()); err != nil {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			continue
		}

		if i > 0 {
			fmt.Fprintln(os.Stdout)
		}
		if _, err := io.WriteString(os.Stdout, out); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
}
