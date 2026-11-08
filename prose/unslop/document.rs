use crate::markdown::Projection;
use crate::text::{normalize, rx, word_count, Mapped, Span, WORD};
use std::collections::HashSet;

#[derive(Clone)]
pub struct Unit {
    pub start: usize,
    pub end: usize,
    pub text: String,
    pub words: usize,
}
pub struct Document {
    pub path: String,
    pub source: Mapped,
    pub visible: Mapped,
    pub structural: Mapped,
    pub headings: Vec<Span>,
    pub bold: Vec<Span>,
    pub parenthetical: Vec<Span>,
    pub word_starts: Vec<usize>,
    pub paragraphs: Vec<Unit>,
    pub sentences: Vec<Unit>,
    line_starts: Vec<usize>,
    suppressions: Vec<(bool, HashSet<String>)>,
}

impl Document {
    pub fn new(path: String, source: String) -> Self {
        let source = Mapped::new(source);
        let mut projection = Projection::new(&source);
        let visible = Mapped::new(projection.visible.iter().collect());
        let structural = Mapped::new(projection.structural.iter().collect());
        let word_starts = rx(WORD).find_iter(&visible.text).map(|m| visible.offset(m.start())).collect();
        let paragraphs = paragraphs(&structural);
        let sentences = paragraphs.iter().flat_map(sentences).collect();
        let mut line_starts = vec![0];
        line_starts.extend(source.chars.iter().enumerate().filter(|(_, &c)| c == '\n').map(|(i, _)| i + 1));
        projection.headings.sort_by_key(|s| s.start);
        let is_visible = |s: &Span| visible.chars[s.start..s.end].iter().any(|c| !c.is_whitespace());
        let bold = projection.bold.into_iter().filter(is_visible).collect();
        let parenthetical = projection.parenthetical.into_iter().filter(is_visible).collect();
        Self {
            path,
            source,
            visible,
            structural,
            word_starts,
            paragraphs,
            sentences,
            line_starts,
            headings: projection.headings,
            bold,
            parenthetical,
            suppressions: suppressions(&projection.suppression),
        }
    }
    pub fn word_index(&self, offset: usize) -> usize {
        self.word_starts.partition_point(|&i| i <= offset).saturating_sub(1)
    }
    pub fn location(&self, offset: usize) -> (usize, usize) {
        let i = self.line_starts.partition_point(|&start| start <= offset).saturating_sub(1);
        (i + 1, offset - self.line_starts[i] + 1)
    }
    pub fn section(&self, offset: usize) -> usize {
        self.headings.partition_point(|s| s.start <= offset)
    }
    pub fn sections<'a>(&self, units: &'a [Unit]) -> Vec<&'a [Unit]> {
        let mut sections = Vec::new();
        let mut start = 0;
        while start < units.len() {
            let section = self.section(units[start].start);
            let mut end = start + 1;
            while end < units.len() && self.section(units[end].start) == section {
                end += 1;
            }
            sections.push(&units[start..end]);
            start = end;
        }
        sections
    }
    pub fn suppressed(&self, offset: usize, rule: &str) -> bool {
        let (line, _) = self.location(offset);
        let (all, selectors) = &self.suppressions[(line - 1).min(self.suppressions.len() - 1)];
        *all || selectors.iter().any(|s| matches!(s.as_str(), "*" | "all") || s == rule || (s.ends_with(".*") && rule.starts_with(&s[..s.len() - 1])))
    }
    pub fn excerpt(&self, line: usize) -> &str {
        let start = self.line_starts[line - 1];
        let end = self.line_starts.get(line).map_or(self.source.chars.len(), |i| i - 1);
        self.source.slice(start, end)
    }
}

fn paragraphs(text: &Mapped) -> Vec<Unit> {
    let mut result = Vec::new();
    let mut start = None;
    let mut end = 0;
    for line in text.lines() {
        if !text.slice(line.start, line.end).trim().is_empty() {
            start.get_or_insert(line.start);
            end = line.end;
            continue;
        }
        if let Some(first) = start.take() {
            append_paragraph(&mut result, text, first, end);
        }
    }
    if let Some(first) = start {
        append_paragraph(&mut result, text, first, end);
    }
    result
}

fn append_paragraph(result: &mut Vec<Unit>, source: &Mapped, start: usize, end: usize) {
    let text = source.slice(start, end).to_owned();
    let words = word_count(&text);
    if words >= 4 {
        result.push(Unit { start, end, text, words });
    }
}

fn abbreviation(chars: &[char], i: usize) -> bool {
    let prefix: String = chars[i.saturating_sub(12)..=i].iter().collect::<String>().to_lowercase();
    ["e.g.", "i.e.", "etc.", "vs.", "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.", "fig.", "no."].iter().any(|s| prefix.ends_with(s)) || rx(r"\b[A-Za-z]\.$").is_match(&prefix)
}

fn sentences(paragraph: &Unit) -> Vec<Unit> {
    let source = Mapped::new(paragraph.text.clone());
    let chars = &source.chars;
    let mut units = Vec::new();
    let mut start = 0;
    let mut i = 0;
    while i < chars.len() {
        if !matches!(chars[i], '!' | '?') && (chars[i] != '.' || abbreviation(chars, i)) {
            i += 1;
            continue;
        }
        let mut end = i + 1;
        while end < chars.len() && ".!?\"'”’)]".contains(chars[end]) {
            end += 1;
        }
        if end < chars.len() && !chars[end].is_whitespace() {
            i += 1;
            continue;
        }
        let mut leading = start;
        let mut trailing = end;
        while leading < trailing && chars[leading].is_whitespace() {
            leading += 1;
        }
        while trailing > leading && chars[trailing - 1].is_whitespace() {
            trailing -= 1;
        }
        let text = normalize(source.slice(leading, trailing));
        let words = word_count(&text);
        if words > 0 {
            units.push(Unit {
                start: paragraph.start + leading,
                end: paragraph.start + trailing,
                text,
                words,
            });
        }
        start = end;
        i = end;
    }
    units
}

fn suppressions(text: &str) -> Vec<(bool, HashSet<String>)> {
    let directive = rx(r"(?i)<!--\s*unslop-(disable-next-line|disable|enable|ignore)(?:\s+([^>]*?))?\s*-->");
    let split = rx(r"[\s,]+");
    let mut disabled_all = false;
    let mut disabled = HashSet::new();
    let mut pending_all = false;
    let mut pending = HashSet::new();
    let mut result = Vec::new();
    for line in text.split('\n') {
        let mut all = disabled_all || pending_all;
        let mut selected: HashSet<String> = disabled.union(&pending).cloned().collect();
        pending_all = false;
        pending.clear();
        for c in directive.captures_iter(line) {
            let value = c.get(2).map_or("", |m| m.as_str()).trim();
            let tokens: HashSet<String> = if value.is_empty() { ["*".to_owned()].into_iter().collect() } else { split.split(value).filter(|s| !s.is_empty()).map(str::to_owned).collect() };
            let selects_all = tokens.contains("*") || tokens.contains("all");
            match c[1].to_lowercase().as_str() {
                "ignore" => {
                    if selects_all {
                        all = true;
                    } else {
                        selected.extend(tokens);
                    }
                }
                "disable-next-line" => {
                    if selects_all {
                        pending_all = true;
                    } else {
                        pending.extend(tokens);
                    }
                }
                "disable" => {
                    if selects_all {
                        disabled_all = true;
                    } else {
                        disabled.extend(tokens);
                    }
                }
                _ => {
                    if selects_all {
                        disabled_all = false;
                        disabled.clear();
                    } else {
                        disabled.retain(|s| !tokens.contains(s));
                    }
                }
            }
        }
        result.push((all, selected));
    }
    result
}
