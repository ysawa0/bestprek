// Run gopls diagnostics as a failing commit check.
package main

import (
	"bytes"
	"fmt"
	"log"
	"os"
	"os/exec"
)

func main() {
	log.SetFlags(0)
	command := exec.Command("gopls", append([]string{"check"}, os.Args[1:]...)...)
	var diagnostics bytes.Buffer
	command.Stdout = &diagnostics
	command.Stderr = os.Stderr
	err := command.Run()
	if _, writeErr := fmt.Fprint(os.Stdout, diagnostics.String()); writeErr != nil {
		log.Fatal(writeErr)
	}
	if err != nil {
		log.Fatal(err)
	}
	// gopls check exits successfully even when it emits diagnostics.
	if diagnostics.Len() > 0 {
		os.Exit(1)
	}
}
