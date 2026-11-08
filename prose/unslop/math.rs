use crate::text::Span;

// Math has punctuation and function arguments, but neither is prose.
pub fn spans(chars: &[char]) -> Vec<Span> {
    let mut spans = Vec::new();
    let mut i = 0;
    while i < chars.len() {
        if chars[i..].starts_with(&['<', '!', '-', '-']) {
            i += 4;
            while i < chars.len() && !chars[i..].starts_with(&['-', '-', '>']) {
                i += 1;
            }
            i = (i + 3).min(chars.len());
            continue;
        }
        if escaped(chars, i) {
            i += 1;
            continue;
        }
        let (close, width, multiline) = match (chars[i], chars.get(i + 1)) {
            ('\\', Some('(')) => (')', 2, false),
            ('\\', Some('[')) => (']', 2, true),
            ('$', Some('$')) => ('$', 2, true),
            ('$', Some(next)) if !next.is_whitespace() => ('$', 1, false),
            _ => {
                i += 1;
                continue;
            }
        };
        let start = i;
        i += width;
        while i < chars.len() {
            if !multiline && chars[i] == '\n' {
                break;
            }
            let closes = if width == 1 {
                chars[i] == '$' && !chars[i - 1].is_whitespace() && !chars.get(i + 1).is_some_and(char::is_ascii_digit)
            } else if close == '$' {
                chars[i] == '$' && chars.get(i + 1) == Some(&'$')
            } else {
                chars[i] == '\\' && chars.get(i + 1) == Some(&close)
            };
            if closes && !escaped(chars, i) {
                i += width;
                spans.push(Span { start, end: i });
                break;
            }
            i += 1;
        }
    }
    spans
}

fn escaped(chars: &[char], offset: usize) -> bool {
    chars[..offset].iter().rev().take_while(|&&ch| ch == '\\').count() % 2 == 1
}
