package main

import (
	"flag"
	"io"
	"log"
	"os"
)

func processReader(reader io.Reader, writer io.Writer) error {
	data, err := io.ReadAll(reader)
	if err != nil {
		return err
	}
	_, err = io.WriteString(writer, stripBold(string(data)))
	return err
}

func main() {
	log.SetFlags(0)
	writeInPlace := flag.Bool("write", false, "rewrite files in place")
	flag.Parse()
	paths := flag.Args()

	if len(paths) == 0 {
		if err := processReader(os.Stdin, os.Stdout); err != nil {
			log.Fatal(err)
		}
		return
	}

	for i, path := range paths {
		if err := processFile(path, *writeInPlace, i > 0); err != nil {
			log.Fatal(err)
		}
	}
}

func processFile(path string, writeInPlace, separator bool) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	out := stripBold(string(data))
	if writeInPlace {
		info, err := os.Stat(path)
		if err != nil {
			return err
		}
		return os.WriteFile(path, []byte(out), info.Mode().Perm())
	}
	if separator {
		out = "\n" + out
	}
	_, err = io.WriteString(os.Stdout, out)
	return err
}
