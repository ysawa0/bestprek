// Run gopls diagnostics as a failing commit check.
package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
)

func main() {
	command := exec.Command("gopls", append([]string{"check"}, os.Args[1:]...)...)
	var diagnostics bytes.Buffer
	command.Stdout = &diagnostics
	command.Stderr = os.Stderr
	if err := command.Run(); err != nil {
		fmt.Fprint(os.Stdout, diagnostics.String())
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Fprint(os.Stdout, diagnostics.String())
	// gopls check exits successfully even when it emits diagnostics.
	if diagnostics.Len() > 0 {
		os.Exit(1)
	}
}
