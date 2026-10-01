use regex::bytes::Regex;
use std::sync::OnceLock;

fn raw_code() -> &'static Regex {
    static PATTERN: OnceLock<Regex> = OnceLock::new();
    PATTERN.get_or_init(|| Regex::new(r"(?is)^<(code|pre|script|style)\b[^>]*>").expect("valid regex"))
}

fn reference() -> &'static Regex {
    static PATTERN: OnceLock<Regex> = OnceLock::new();
    PATTERN.get_or_init(|| Regex::new(r"^ {0,3}\[[^\]]+\]:").expect("valid regex"))
}

pub fn run_length(text: &[u8], start: usize) -> usize {
    text[start..].iter().take_while(|&&byte| byte == text[start]).count()
}

fn thematic_break(line: &[u8]) -> bool {
    let compact: Vec<u8> = line.iter().copied().filter(|byte| !matches!(byte, b' ' | b'\t' | b'\r' | b'\n')).collect();
    compact.len() >= 3 && matches!(compact[0], b'*' | b'_') && run_length(&compact, 0) == compact.len()
}

fn inline_code_end(text: &[u8], start: usize) -> usize {
    let length = run_length(text, start);
    let mut cursor = start + length;
    while cursor < text.len() {
        if text[cursor] != b'`' {
            cursor += 1;
            continue;
        }
        let closing = run_length(text, cursor);
        cursor += closing;
        if closing == length {
            return cursor;
        }
    }
    start + length
}

fn link_end(text: &[u8], start: usize) -> usize {
    let mut depth = 1;
    let mut quote = None;
    let mut cursor = start + 1;
    while cursor < text.len() {
        let char = text[cursor];
        cursor += 1;
        if char == b'\\' {
            cursor += 1;
            continue;
        }
        if let Some(open) = quote {
            if char == open {
                quote = None;
            }
            continue;
        }
        match char {
            b'"' | b'\'' => quote = Some(char),
            b'(' => depth += 1,
            b')' => {
                depth -= 1;
                if depth == 0 {
                    return cursor;
                }
            }
            _ => {}
        }
    }
    start
}

fn find(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack.windows(needle.len()).position(|window| window == needle)
}

fn html_end(text: &[u8], start: usize) -> usize {
    let remaining = &text[start..];
    if remaining.starts_with(b"<!--") {
        return find(remaining, b"-->").map_or(text.len(), |end| start + end + 3);
    }
    if let Some(found) = raw_code().captures(remaining) {
        let closing = [b"</", found[1].to_ascii_lowercase().as_slice(), b">"].concat();
        return find(&remaining.to_ascii_lowercase(), &closing).map_or(text.len(), |end| start + end + closing.len());
    }
    let mut quote = None;
    for (cursor, &char) in text.iter().enumerate().skip(start + 1) {
        if let Some(open) = quote {
            if char == open {
                quote = None;
            }
            continue;
        }
        match char {
            b'\'' | b'"' => quote = Some(char),
            b'>' => return cursor + 1,
            b'\n' => return start,
            _ => {}
        }
    }
    start
}

struct Protector<'a> {
    input: &'a [u8],
    protected: Vec<bool>,
    fence: Option<(u8, usize)>,
}

impl Protector<'_> {
    fn protect(&mut self, start: usize, end: usize) {
        self.protected[start..end].fill(true);
    }

    fn update_fence(&mut self, trimmed: &[u8], indented: bool) {
        let Some(&marker) = trimmed.first() else { return };
        if indented || !matches!(marker, b'`' | b'~') {
            return;
        }
        let length = run_length(trimmed, 0);
        match self.fence {
            None if length >= 3 => self.fence = Some((marker, length)),
            Some((open, open_length)) if open == marker && length >= open_length && trimmed[length..].iter().all(u8::is_ascii_whitespace) => self.fence = None,
            _ => {}
        }
    }

    fn protect_line(&mut self, start: usize) -> (usize, bool) {
        let end = self.input[start..].iter().position(|&byte| byte == b'\n').map_or(self.input.len(), |newline| start + newline + 1);
        let line = &self.input[start..end];
        let leading_spaces = line.iter().take_while(|&&byte| byte == b' ').count();
        let indented = leading_spaces >= 4 || line[leading_spaces..].starts_with(b"\t");
        let trimmed = &line[line.iter().take_while(|byte| matches!(byte, b' ' | b'>' | b'\t')).count()..];
        let was_fenced = self.fence.is_some();
        self.update_fence(trimmed, indented);
        if was_fenced || self.fence.is_some() || indented {
            return (end, true);
        }
        (end, thematic_break(trimmed) || reference().is_match(line))
    }
}

fn inline_protection_end(input: &[u8], start: usize) -> usize {
    match input[start] {
        b'\\' if start + 1 < input.len() => start + 2,
        b'`' => inline_code_end(input, start),
        b'<' => html_end(input, start),
        b'(' if start > 0 && input[start - 1] == b']' => link_end(input, start),
        _ => start,
    }
}

// Mark syntax whose literal content must never be rewritten as emphasis.
pub fn protected_markdown(input: &[u8]) -> Vec<bool> {
    let mut protector = Protector {
        input,
        protected: vec![false; input.len()],
        fence: None,
    };
    let mut i = 0;
    while i < input.len() {
        if i == 0 || input[i - 1] == b'\n' {
            let (end, protect) = protector.protect_line(i);
            if protect {
                protector.protect(i, end);
                i = end;
                continue;
            }
        }
        let end = inline_protection_end(input, i);
        if end > i {
            protector.protect(i, end);
            i = end;
        } else {
            i += 1;
        }
    }
    protector.protected
}
