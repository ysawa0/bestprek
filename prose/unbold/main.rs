mod emphasis;
mod markdown;

use emphasis::strip_bold;
use std::io::{self, Read, Write};

fn run() -> io::Result<()> {
    let mut paths: Vec<String> = std::env::args().skip(1).collect();
    let write = paths.first().is_some_and(|arg| arg == "--write");
    if write {
        paths.remove(0);
    }
    let mut stdout = io::stdout().lock();
    if paths.is_empty() {
        let mut input = Vec::new();
        io::stdin().read_to_end(&mut input)?;
        return stdout.write_all(&strip_bold(&input));
    }
    for (index, path) in paths.iter().enumerate() {
        let context = |error: io::Error| io::Error::new(error.kind(), format!("{path}: {error}"));
        let output = strip_bold(&std::fs::read(path).map_err(context)?);
        if write {
            std::fs::write(path, output).map_err(context)?;
            continue;
        }
        if index > 0 {
            stdout.write_all(b"\n")?;
        }
        stdout.write_all(&output)?;
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("unbold: {error}");
        std::process::exit(1);
    }
}
