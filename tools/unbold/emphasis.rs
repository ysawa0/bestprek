use crate::markdown::{protected_markdown, run_length};
use regex::Regex;
use std::sync::OnceLock;

#[derive(Clone, Copy)]
struct Delimiter {
    start: usize,
    length: usize,
    marker: u8,
    can_open: bool,
    can_close: bool,
}

fn punctuation(char: char) -> bool {
    static PATTERN: OnceLock<Regex> = OnceLock::new();
    let pattern = PATTERN.get_or_init(|| Regex::new(r"^[\p{P}\p{S}]$").expect("valid regex"));
    pattern.is_match(char.encode_utf8(&mut [0; 4]))
}

// Decode the characters around a delimiter run; invalid UTF-8 reads as U+FFFD.
fn surrounding(text: &[u8], start: usize, end: usize) -> (char, char) {
    let decode = |bytes: &[u8]| std::str::from_utf8(bytes).ok().and_then(|text| text.chars().next());
    let before = if start == 0 { Some(' ') } else { (1..=start.min(4)).find_map(|width| decode(&text[start - width..start])) };
    let after = if end == text.len() { Some(' ') } else { (1..=(text.len() - end).min(4)).find_map(|width| decode(&text[end..end + width])) };
    (before.unwrap_or(char::REPLACEMENT_CHARACTER), after.unwrap_or(char::REPLACEMENT_CHARACTER))
}

fn new_delimiter(text: &[u8], start: usize, length: usize) -> Delimiter {
    let (before, after) = surrounding(text, start, start + length);
    let left = !after.is_whitespace() && (!punctuation(after) || before.is_whitespace() || punctuation(before));
    let right = !before.is_whitespace() && (!punctuation(before) || after.is_whitespace() || punctuation(after));
    if text[start] == b'_' {
        return Delimiter {
            start,
            length,
            marker: b'_',
            can_open: left && (!right || punctuation(before)),
            can_close: right && (!left || punctuation(after)),
        };
    }
    Delimiter {
        start,
        length,
        marker: b'*',
        can_open: left,
        can_close: right,
    }
}

fn pairs(open: &Delimiter, close: &Delimiter) -> bool {
    if !open.can_open || open.marker != close.marker {
        return false;
    }
    // The rule of three prevents ambiguous runs from pairing across emphasis.
    !(open.can_close || close.can_open) || (open.length + close.length) % 3 != 0 || (open.length % 3 == 0 && close.length % 3 == 0)
}

fn consume(stack: &mut Vec<Delimiter>, mut close: Delimiter, removed: &mut [bool]) -> Delimiter {
    while close.can_close && close.length > 0 {
        let Some(index) = stack.iter().rposition(|open| pairs(open, &close)) else { break };
        let open = &mut stack[index];
        let mut count = 1;
        if open.length >= 2 && close.length >= 2 {
            count = 2;
            removed[open.start + open.length - count..open.start + open.length].fill(true);
            removed[close.start..close.start + count].fill(true);
        }
        open.length -= count;
        close.start += count;
        close.length -= count;
        let keep = if open.length == 0 { index } else { index + 1 };
        stack.truncate(keep);
    }
    close
}

// Remove paired strong-emphasis delimiters, leaving single emphasis intact.
pub fn strip_bold(input: &[u8]) -> Vec<u8> {
    let protected = protected_markdown(input);
    let mut removed = vec![false; input.len()];
    let mut stack = Vec::new();
    let mut i = 0;
    while i < input.len() {
        if i == 0 || input[i - 1] == b'\n' {
            let line = input[i..].split(|&byte| byte == b'\n').next().unwrap_or_default();
            if line.iter().all(|byte| matches!(byte, b' ' | b'\t' | b'\r')) {
                stack.clear();
            }
        }
        if protected[i] || !matches!(input[i], b'*' | b'_') {
            i += 1;
            continue;
        }
        let length = run_length(input, i);
        let current = consume(&mut stack, new_delimiter(input, i, length), &mut removed);
        if current.can_open && current.length > 0 {
            stack.push(current);
        }
        i += length;
    }
    input.iter().zip(removed).filter(|(_, removed)| !removed).map(|(&byte, _)| byte).collect()
}
