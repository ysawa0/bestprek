package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"strings"
)

func stripBold(input string) string {
	out := strings.ReplaceAll(input, "**", "")
	out = strings.ReplaceAll(out, "__", "")
	return out
}

func processReader(reader io.Reader, writer io.Writer) error {
	data, err := io.ReadAll(reader)
	if err != nil {
		return err
	}
	_, err = io.WriteString(writer, stripBold(string(data)))
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
		out := stripBold(string(data))
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
