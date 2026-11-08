use regex::Regex;
use std::collections::HashMap;
use std::sync::{Arc, Mutex, OnceLock};

pub fn rx(pattern: &str) -> Arc<Regex> {
    static CACHE: OnceLock<Mutex<HashMap<String, Arc<Regex>>>> = OnceLock::new();
    let mut cache = CACHE.get_or_init(|| Mutex::new(HashMap::new())).lock().unwrap();
    cache.entry(pattern.to_owned()).or_insert_with(|| Arc::new(Regex::new(pattern).unwrap())).clone()
}

pub fn insensitive(pattern: &str) -> Arc<Regex> {
    // Python's IGNORECASE also treats dotted and dotless I as ASCII I.
    let mut converted = String::from("(?i)");
    let mut escaped = false;
    let mut class = false;
    for ch in pattern.chars() {
        if escaped {
            converted.push(ch);
            escaped = false;
        } else if ch == '\\' {
            converted.push(ch);
            escaped = true;
        } else if ch == '[' {
            class = true;
            converted.push(ch);
        } else if ch == ']' {
            class = false;
            converted.push(ch);
        } else if !class && matches!(ch, 'i' | 'I') {
            converted.push_str("[iİı]");
        } else {
            converted.push(ch);
        }
    }
    rx(&converted.replace("[A-Za-z", "[İıA-Za-z").replace("[A-Z]", "[İıA-Z]"))
}

pub const WORD: &str = r"[A-Za-z0-9]+(?:[’'][A-Za-z0-9]+)*(?:-[A-Za-z0-9]+)*";

pub fn word_count(text: &str) -> usize {
    rx(WORD).find_iter(text).count()
}
pub fn normalize(text: &str) -> String {
    rx(r"\s+").replace_all(text, " ").trim().to_owned()
}

#[derive(Clone, Copy, Debug)]
pub struct Span {
    pub start: usize,
    pub end: usize,
}

pub struct Mapped {
    pub text: String,
    pub chars: Vec<char>,
    starts: Vec<usize>,
}

impl Mapped {
    pub fn new(text: String) -> Self {
        let mut starts: Vec<usize> = text.char_indices().map(|(i, _)| i).collect();
        starts.push(text.len());
        Self { chars: text.chars().collect(), text, starts }
    }
    pub fn offset(&self, byte: usize) -> usize {
        self.starts.partition_point(|&i| i <= byte) - 1
    }
    pub fn slice(&self, start: usize, end: usize) -> &str {
        &self.text[self.starts[start]..self.starts[end]]
    }
    pub fn span(&self, found: regex::Match<'_>) -> Span {
        Span {
            start: self.offset(found.start()),
            end: self.offset(found.end()),
        }
    }
    pub fn lines(&self) -> Vec<Span> {
        let mut result = Vec::new();
        let mut start = 0;
        for (i, &ch) in self.chars.iter().enumerate() {
            if ch == '\n' {
                let end = if i > start && self.chars[i - 1] == '\r' { i - 1 } else { i };
                result.push(Span { start, end });
                start = i + 1;
            }
        }
        result.push(Span { start, end: self.chars.len() });
        result
    }
}
