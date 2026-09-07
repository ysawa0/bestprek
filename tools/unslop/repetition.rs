use crate::config::Resolved;
use crate::document::{Document, Unit};
use crate::rules::{clusters, finding, Finding};
use crate::text::{insensitive, rx, WORD};
use std::collections::HashSet;

pub fn check(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    match rule.rule.checker.as_str() {
        "sentence_openers" => openers(doc, rule, true),
        "paragraph_openers" => openers(doc, rule, false),
        "transition_repetition" => transitions(doc, rule),
        "loaded_word_repetition" => loaded(doc, rule),
        "short_sentence_run" => short(doc, rule),
        "uniform_sentence_length" => uniform(doc, rule),
        _ => unreachable!(),
    }
}

fn opener(text: &str) -> Option<String> {
    let words: Vec<String> = rx(WORD).find_iter(text).take(2).map(|m| m.as_str().to_lowercase().replace('’', "'")).collect();
    if words.len() == 2 {
        Some(words.join(" "))
    } else {
        None
    }
}

fn repeated(units: &[Unit], consecutive: usize, window: usize, count: usize) -> Vec<(String, Vec<&Unit>)> {
    let keys: Vec<Option<String>> = units.iter().map(|u| opener(&u.text)).collect();
    let mut consumed = HashSet::new();
    let mut result = Vec::new();
    let mut i = 0;
    while i < units.len() {
        let Some(key) = &keys[i] else {
            i += 1;
            continue;
        };
        let mut end = i + 1;
        while end < units.len() && keys[end] == keys[i] {
            end += 1;
        }
        if end - i >= consecutive {
            result.push((key.clone(), units[i..end].iter().collect()));
            consumed.extend(i..end);
        }
        i = end;
    }
    for start in 0..units.len() {
        if consumed.contains(&start) || keys[start].is_none() {
            continue;
        }
        let matches: Vec<usize> = (start..units.len().min(start + window)).filter(|i| !consumed.contains(i) && keys[*i] == keys[start]).collect();
        if matches.len() >= count {
            result.push((keys[start].clone().unwrap(), matches.iter().map(|&i| &units[i]).collect()));
            consumed.extend(matches);
        }
    }
    result
}

fn openers(doc: &Document, rule: &Resolved, sentence: bool) -> Vec<Finding> {
    let (units, window, noun, suggestion) = if sentence {
        (&doc.sentences, "window_sentences", "sentences", "Merge a sentence or vary the grammatical opening unless the repetition is deliberate anaphora.")
    } else {
        (&doc.paragraphs, "window_paragraphs", "paragraphs", "Vary the paragraph entry or combine paragraphs that make the same move.")
    };
    doc.sections(units)
        .iter()
        .flat_map(|section| repeated(section, rule.number("consecutive"), rule.number(window), rule.number("window_count")))
        .map(|(key, group)| finding(group[1].start, group.last().unwrap().end, format!("{} {noun} repeatedly open with '{key}'.", group.len()), suggestion))
        .collect()
}

const TRANSITIONS: &[&str] = &[
    "moreover",
    "furthermore",
    "additionally",
    "in addition",
    "ultimately",
    "in essence",
    "at its core",
    "that said",
    "on the other hand",
    "the key takeaway",
    "here's the thing",
    "here is the thing",
];

fn transitions(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let max = rule.number("max");
    let window = rule.number("window_words");
    let mut result = Vec::new();
    for phrase in TRANSITIONS {
        let mut offsets = Vec::new();
        for m in insensitive(&format!(r"\b{}\b", regex::escape(phrase))).find_iter(&doc.visible.text) {
            let pos = doc.visible.offset(m.start());
            let mut start = pos;
            while start > 0 && doc.visible.chars[start - 1].is_whitespace() {
                start -= 1;
            }
            if start == 0 || ".!?".contains(doc.visible.chars[start - 1]) {
                offsets.push(start);
                continue;
            }
            if let Some(i) = doc.visible.chars[start..pos].iter().position(|&c| c == '\n') {
                offsets.push(start + i + 1);
            }
        }
        for group in clusters(doc, &offsets, max, window) {
            result.push(finding(
                group[max],
                group.last().unwrap() + phrase.len(),
                format!("The transition '{phrase}' appears {} times within {window} words.", group.len()),
                "Delete a transition where paragraph order already makes the relationship clear.",
            ));
        }
    }
    result
}

fn loaded(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let stems = [
        ("delve", r"\bdelv(?:e|es|ed|ing)\b"),
        ("pivotal", r"\bpivotal\b"),
        ("nuanced", r"\bnuanced?\b"),
        ("robust", r"\brobust\b"),
        ("seamless", r"\bseamless(?:ly)?\b"),
        ("transformative", r"\btransformative\b"),
        ("landscape", r"\blandscape\b"),
        ("tapestry", r"\btapestry\b"),
        ("underscore", r"\bunderscor(?:e|es|ed|ing)\b"),
        ("showcase", r"\bshowcas(?:e|es|ed|ing)\b"),
        ("foster", r"\bfoster(?:s|ed|ing)?\b"),
        ("elevate", r"\belevat(?:e|es|ed|ing)\b"),
        ("unlock", r"\bunlock(?:s|ed|ing)?\b"),
    ];
    let max = rule.number("max");
    let window = rule.number("window_words");
    let mut result = Vec::new();
    for (label, pattern) in stems {
        let offsets: Vec<usize> = insensitive(pattern).find_iter(&doc.visible.text).map(|m| doc.visible.offset(m.start())).collect();
        for group in clusters(doc, &offsets, max, window) {
            result.push(finding(
                group[max],
                group.last().unwrap() + label.len(),
                format!("The loaded word '{label}' appears {} times within {window} words.", group.len()),
                "Replace at least one use with the concrete property you mean.",
            ));
        }
    }
    result
}

fn short(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let max = rule.number("max_words");
    let mut result = Vec::new();
    for section in doc.sections(&doc.sentences) {
        let mut i = 0;
        while i < section.len() {
            if section[i].words > max {
                i += 1;
                continue;
            }
            let mut end = i + 1;
            while end < section.len() && section[end].words <= max {
                end += 1;
            }
            if end - i >= rule.number("minimum_run") {
                result.push(finding(
                    section[i + 1].start,
                    section[end - 1].end,
                    format!("{} consecutive sentences contain at most {max} words each, creating a manufactured staccato rhythm.", end - i),
                    "Combine related fragments and reserve the short sentence for emphasis.",
                ));
            }
            i = end;
        }
    }
    result
}

fn uniform(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let lengths: Vec<f64> = doc.sentences.iter().filter(|s| s.words >= 3).map(|s| s.words as f64).collect();
    if lengths.len() < rule.number("minimum_sentences") {
        return Vec::new();
    }
    let mean = lengths.iter().sum::<f64>() / lengths.len() as f64;
    let variance = lengths.iter().map(|n| (n - mean).powi(2)).sum::<f64>() / lengths.len() as f64;
    let cv = variance.sqrt() / mean;
    if cv >= rule.float("maximum_cv") {
        return Vec::new();
    }
    vec![finding(
        doc.sentences[0].start,
        doc.sentences.last().unwrap().end,
        format!("Sentence lengths are unusually uniform (coefficient of variation {cv:.2} across {} sentences).", lengths.len()),
        "Mix short assertions with longer explanatory sentences where the content supports it.",
    )]
}
