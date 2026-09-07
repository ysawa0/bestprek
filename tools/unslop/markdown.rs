use crate::text::{insensitive, rx, Mapped, Span};
use std::collections::HashSet;

pub struct Projection {
    pub visible: Vec<char>,
    pub structural: Vec<char>,
    pub suppression: String,
    pub headings: Vec<Span>,
    pub bold: Vec<Span>,
    pub parenthetical: Vec<Span>,
}

impl Projection {
    pub fn new(source: &Mapped) -> Self {
        let mut out = Self {
            visible: source.chars.clone(),
            structural: source.chars.clone(),
            suppression: String::new(),
            headings: Vec::new(),
            bold: Vec::new(),
            parenthetical: Vec::new(),
        };
        let lines = source.lines();
        out.front_matter(source, &lines);
        out.fences(source, &lines);
        out.raw_code(source);
        out.line_constructs(source, &lines);
        out.inline(source);
        for span in crate::math::spans(&out.visible) {
            out.mask(span, true, true);
            out.headings.retain(|heading| heading.start < span.start || heading.start >= span.end);
        }
        out.suppression = out.visible.iter().collect();
        out.mask_matches(source, r"(?s)<!--.*?-->");
        let visible = Mapped::new(out.visible.iter().collect());
        out.bold = bold_spans(&visible);
        out.parenthetical = rx(r"\([^()\n]{2,120}\)").find_iter(&visible.text).filter(|m| !rx(r"^\([A-Za-z]*[0-9]+[A-Za-z]?\)$").is_match(m.as_str())).map(|m| visible.span(m)).collect();
        for target in [&mut out.visible, &mut out.structural] {
            for ch in target {
                if matches!(*ch, '*' | '_' | '`') {
                    *ch = ' ';
                }
            }
        }
        out
    }

    fn mask(&mut self, span: Span, visible: bool, structural: bool) {
        for (target, enabled) in [(&mut self.visible, visible), (&mut self.structural, structural)] {
            if enabled {
                for ch in &mut target[span.start..span.end] {
                    if !matches!(*ch, '\r' | '\n') {
                        *ch = ' ';
                    }
                }
            }
        }
    }

    fn mask_matches(&mut self, source: &Mapped, pattern: &str) {
        for m in rx(pattern).find_iter(&source.text) {
            self.mask(source.span(m), true, true);
        }
    }

    fn front_matter(&mut self, source: &Mapped, lines: &[Span]) {
        if source.slice(lines[0].start, lines[0].end).trim() != "---" {
            return;
        }
        for line in lines.iter().take(200).skip(1) {
            if matches!(source.slice(line.start, line.end).trim(), "---" | "...") {
                self.mask(Span { start: 0, end: line.end }, true, true);
                return;
            }
        }
    }

    fn fences(&mut self, source: &Mapped, lines: &[Span]) {
        let mut open: Option<(char, usize, usize)> = None;
        let marker = rx(r"^ {0,3}(`{3,}|~{3,})");
        for line in lines {
            let text = source.slice(line.start, line.end);
            if let Some((ch, count, start)) = open {
                if rx(&format!(r"^ {{0,3}}{}{{{},}}\s*$", ch, count)).is_match(text) {
                    self.mask(Span { start, end: line.end }, true, true);
                    open = None;
                }
                continue;
            }
            if let Some(c) = marker.captures(text) {
                let token = c.get(1).unwrap().as_str();
                open = Some((token.chars().next().unwrap(), token.len(), line.start));
            }
        }
        if let Some((_, _, start)) = open {
            self.mask(Span { start, end: source.chars.len() }, true, true);
        }
    }

    fn raw_code(&mut self, source: &Mapped) {
        let mut end = 0;
        for c in insensitive(r"<(pre|script|style|code)\b[^>]*>").captures_iter(&source.text) {
            let opening = c.get(0).unwrap();
            if opening.start() < end {
                continue;
            }
            let close = insensitive(&format!(r"</{}\s*>", &c[1]));
            if let Some(m) = close.find_at(&source.text, opening.end()) {
                end = m.end();
                self.mask(
                    Span {
                        start: source.offset(opening.start()),
                        end: source.offset(end),
                    },
                    true,
                    true,
                );
            }
        }
    }

    fn line_constructs(&mut self, source: &Mapped, lines: &[Span]) {
        let separator = rx(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$");
        let mut tables = HashSet::new();
        for (i, line) in lines.iter().enumerate() {
            if !separator.is_match(source.slice(line.start, line.end)) {
                continue;
            }
            tables.insert(i);
            if i > 0 && source.slice(lines[i - 1].start, lines[i - 1].end).contains('|') {
                tables.insert(i - 1);
            }
            for (j, candidate) in lines.iter().enumerate().skip(i + 1) {
                let text = source.slice(candidate.start, candidate.end);
                if text.trim().is_empty() || !text.contains('|') {
                    break;
                }
                tables.insert(j);
            }
        }
        let mut titles = HashSet::new();
        let mut underlines = HashSet::new();
        for i in 1..lines.len() {
            let line = lines[i];
            if rx(r"^ {0,3}(?:=+|-+)\s*$").is_match(source.slice(line.start, line.end)) && !source.slice(lines[i - 1].start, lines[i - 1].end).trim().is_empty() {
                titles.insert(i - 1);
                underlines.insert(i);
                self.headings.push(lines[i - 1]);
            }
        }
        for (i, &line) in lines.iter().enumerate() {
            let text = source.slice(line.start, line.end);
            if !text.trim().is_empty() && self.visible[line.start..line.end].iter().all(|c| c.is_whitespace()) {
                continue;
            }
            if tables.contains(&i) || underlines.contains(&i) {
                self.mask(line, true, true);
                continue;
            }
            if titles.contains(&i) {
                self.mask(line, false, true);
                continue;
            }
            if rx(r"^ {0,3}>|^(?: {4}|\t)|^\s*(?:import|export)\s+|^ {0,3}\[[^\]]+\]:\s*\S+|^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$").is_match(text) {
                self.mask(line, true, true);
                continue;
            }
            if let Some(m) = rx(r"^ {0,3}#{1,6}(?:[ \t]+|$)").find(text) {
                self.headings.push(line);
                self.mask(line, false, true);
                self.mask(
                    Span {
                        start: line.start,
                        end: line.start + text[..m.end()].chars().count(),
                    },
                    true,
                    false,
                );
                continue;
            }
            if let Some(m) = rx(r"^\s*(?:[-+*]|\d+[.)])\s+").find(text) {
                self.mask(line, false, true);
                self.mask(
                    Span {
                        start: line.start,
                        end: line.start + text[..m.end()].chars().count(),
                    },
                    true,
                    false,
                );
            }
        }
    }

    fn inline(&mut self, source: &Mapped) {
        let mut end = 0;
        for m in rx(r"<!--|`+").find_iter(&source.text) {
            if m.start() < end {
                continue;
            }
            if m.as_str() == "<!--" {
                end = source.text[m.end()..].find("-->").map_or(source.text.len(), |i| m.end() + i + 3);
                continue;
            }
            if self.visible[source.offset(m.start())] == ' ' {
                continue;
            }
            if let Some(close) = source.text[m.end()..].find(m.as_str()) {
                end = m.end() + close + m.len();
                self.mask(
                    Span {
                        start: source.offset(m.start()),
                        end: source.offset(end),
                    },
                    true,
                    true,
                );
            }
        }
        self.mask_matches(source, r"!\[[^\]]*\]\([^\n)]*\)");
        for c in rx(r"\[[^\]\n]+\](\([^\n)]*\))").captures_iter(&source.text) {
            let m = c.get(0).unwrap();
            if m.start() > 0 && source.text.as_bytes()[m.start() - 1] == b'!' {
                continue;
            }
            self.mask(source.span(c.get(1).unwrap()), true, true);
        }
        self.mask_matches(source, r"(?i)<(?:(?:https?|mailto):[^>]+)>");
        self.mask_matches(source, r"(?i)\b(?:https?://|www\.)[^\s<>()]+");
        self.mask_matches(source, r"</?[A-Za-z][^>\n]*>");
    }
}

fn bold_spans(source: &Mapped) -> Vec<Span> {
    let mut spans = Vec::new();
    let chars = &source.chars;
    let mut i = 0;
    while i + 2 < chars.len() {
        let marker = chars[i];
        if !matches!(marker, '*' | '_') || chars[i + 1] != marker || chars[i + 2].is_whitespace() || (i > 0 && chars[i - 1] == '\\') {
            i += 1;
            continue;
        }
        let close = (i + 3..chars.len().saturating_sub(1)).find(|&j| chars[j] == marker && chars[j + 1] == marker && !chars[j - 1].is_whitespace());
        if let Some(j) = close {
            if !source.slice(i, j + 2).contains("\n\n") {
                spans.push(Span { start: i, end: j + 2 });
            }
            i = j + 2;
        } else {
            i += 1;
        }
    }
    spans
}
