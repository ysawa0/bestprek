use crate::config::{catalogue, read_config, resolve, severity};
use crate::document::Document;
use serde::Serialize;
use std::io::{self, Write};

#[derive(Default)]
struct Args {
    files: Vec<String>,
    config: Option<String>,
    preset: Option<String>,
    format: String,
    fail_level: Option<String>,
    no_excerpts: bool,
    list_rules: bool,
    version: bool,
    help: bool,
}

fn parse() -> Result<Args, String> {
    let mut out = Args { format: "text".to_owned(), ..Args::default() };
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        if arg == "--" {
            out.files.extend(args);
            break;
        }
        if !arg.starts_with('-') || arg == "-" {
            out.files.push(arg);
            continue;
        }
        let (name, inline) = arg.split_once('=').map_or((arg.as_str(), None), |(k, v)| (k, Some(v.to_owned())));
        match name {
            "--no-excerpts" => out.no_excerpts = true,
            "--list-rules" => out.list_rules = true,
            "--version" => out.version = true,
            "--help" | "-h" => out.help = true,
            "--config" | "--preset" | "--format" | "--fail-level" => {
                let value = inline.or_else(|| args.next()).ok_or_else(|| format!("argument {name}: expected one argument"))?;
                let allowed: &[&str] = match name {
                    "--preset" => &["recommended", "strict"],
                    "--format" => &["text", "json", "github"],
                    "--fail-level" => &["info", "warning", "error", "none"],
                    _ => &[],
                };
                if !allowed.is_empty() && !allowed.contains(&value.as_str()) {
                    return Err(format!("argument {name}: invalid choice: '{value}'"));
                }
                match name {
                    "--config" => out.config = Some(value),
                    "--preset" => out.preset = Some(value),
                    "--format" => out.format = value,
                    _ => out.fail_level = Some(value),
                }
            }
            _ => return Err(format!("unrecognized arguments: {arg}")),
        }
    }
    Ok(out)
}

#[derive(Serialize)]
struct Diagnostic {
    path: String,
    line: usize,
    column: usize,
    end_line: usize,
    end_column: usize,
    severity: String,
    rule: String,
    message: String,
    suggestion: Option<String>,
    #[serde(skip)]
    start: usize,
    #[serde(skip)]
    excerpt: String,
}

fn lint(args: &Args) -> Result<(Vec<Diagnostic>, String), String> {
    let config = read_config(args.config.as_deref())?;
    let preset = args.preset.as_deref().or_else(|| config.get("preset").and_then(|v| v.as_str())).unwrap_or("recommended");
    let fail_level = args.fail_level.as_deref().or_else(|| config.get("fail_level").and_then(|v| v.as_str())).unwrap_or("info").to_owned();
    let rules = resolve(preset, &config)?;
    let mut diagnostics = Vec::new();
    for path in &args.files {
        let source = std::fs::read_to_string(path).map_err(|e| format!("cannot read {path}: {e}"))?.replace("\r\n", "\n").replace('\r', "\n");
        let doc = Document::new(path.clone(), source);
        for rule in &rules {
            if rule.severity == "off" {
                continue;
            }
            for found in crate::rules::check(&doc, rule) {
                if doc.suppressed(found.start, &rule.rule.id) {
                    continue;
                }
                let (line, column) = doc.location(found.start);
                let (end_line, end_column) = doc.location(found.start.max(found.end.saturating_sub(1)));
                diagnostics.push(Diagnostic {
                    path: doc.path.clone(),
                    line,
                    column,
                    end_line,
                    end_column: end_column + 1,
                    severity: rule.severity.clone(),
                    rule: rule.rule.id.clone(),
                    message: found.message,
                    suggestion: found.suggestion,
                    start: found.start,
                    excerpt: if args.no_excerpts || args.format != "text" { String::new() } else { doc.excerpt(line).to_owned() },
                });
            }
        }
    }
    diagnostics.sort_by(|a, b| (&a.path, a.start, -severity(&a.severity), &a.rule).cmp(&(&b.path, b.start, -severity(&b.severity), &b.rule)));
    Ok((diagnostics, fail_level))
}

fn escape(value: &str) -> String {
    value.replace('%', "%25").replace('\r', "%0D").replace('\n', "%0A").replace(':', "%3A").replace(',', "%2C")
}

fn print(output: &mut impl Write, args: &Args, diagnostics: &[Diagnostic]) -> io::Result<()> {
    if args.format == "json" {
        serde_json::to_writer_pretty(&mut *output, diagnostics)?;
        return writeln!(output);
    }
    for item in diagnostics {
        if args.format == "github" {
            let level = match item.severity.as_str() {
                "error" => "error",
                "warning" => "warning",
                _ => "notice",
            };
            let mut message = item.message.clone();
            if let Some(suggestion) = &item.suggestion {
                message.push_str(&format!(" Suggestion: {suggestion}"));
            }
            writeln!(
                output,
                "::{level} file={},line={},col={},endLine={},endColumn={},title={}::{}",
                escape(&item.path),
                item.line,
                item.column,
                item.end_line,
                item.end_column,
                escape(&format!("unslop/{}", item.rule)),
                escape(&message)
            )?;
            continue;
        }
        writeln!(output, "{}:{}:{}: {} [{}] {}", item.path, item.line, item.column, item.severity, item.rule, item.message)?;
        if let Some(suggestion) = &item.suggestion {
            writeln!(output, "  suggestion: {suggestion}")?;
        }
        if !item.excerpt.is_empty() {
            writeln!(output, "  {}", item.excerpt.trim_end())?;
        }
    }
    if args.format == "text" && !diagnostics.is_empty() {
        let count = |level: &str| diagnostics.iter().filter(|d| d.severity == level).count();
        writeln!(output, "\nunslop: {} diagnostics ({} error, {} warning, {} info)", diagnostics.len(), count("error"), count("warning"), count("info"))?;
    }
    Ok(())
}

fn run(output: &mut impl Write) -> Result<i32, String> {
    let args = parse()?;
    if args.version {
        writeln!(output, "unslop {}", env!("CARGO_PKG_VERSION").strip_suffix(".0").unwrap_or(env!("CARGO_PKG_VERSION"))).map_err(|e| e.to_string())?;
        return Ok(0);
    }
    if args.help {
        writeln!(output, "Usage: unslop [OPTIONS] [FILE ...]\n\nDeterministically lint Markdown for canned, repetitive, or bloated prose.\n\n  --config PATH\n  --preset recommended|strict\n  --format text|json|github\n  --fail-level info|warning|error|none\n  --no-excerpts\n  --list-rules\n  --version\n  -h, --help").map_err(|e| e.to_string())?;
        return Ok(0);
    }
    if args.list_rules {
        for rule in catalogue() {
            writeln!(output, "{:<38} recommended={:<7} strict={:<7} {}", rule.id, rule.recommended_severity, rule.strict_severity.as_ref().unwrap_or(&rule.recommended_severity), rule.summary).map_err(|e| e.to_string())?;
        }
        return Ok(0);
    }
    if args.files.is_empty() {
        return Err("no files provided".to_owned());
    }
    let (diagnostics, fail_level) = lint(&args)?;
    print(output, &args, &diagnostics).map_err(|e| e.to_string())?;
    Ok(i32::from(fail_level != "none" && diagnostics.iter().any(|d| severity(&d.severity) >= severity(&fail_level))))
}

pub fn main() -> i32 {
    let mut output = io::BufWriter::new(io::stdout().lock());
    match run(&mut output) {
        Ok(status) => status,
        Err(error) => {
            eprintln!("unslop: {error}");
            2
        }
    }
}
