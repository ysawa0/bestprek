use crate::config::Resolved;
use crate::document::{Document, Unit};
use crate::rules::{clusters, finding, Finding};
use crate::text::{insensitive, normalize, rx, word_count, Span, WORD};

pub fn check(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    match rule.rule.checker.as_str() {
        "question_answer" => questions(doc, rule, true),
        "question_density" => questions(doc, rule, false),
        "echoed_clauses" => doc.sentences.iter().filter_map(|s| echoed(s, doc, rule)).collect(),
        "tricolon_density" => tricolons(doc, rule),
        _ => unreachable!(),
    }
}

fn questions(doc: &Document, rule: &Resolved, paired: bool) -> Vec<Finding> {
    let mut spans = Vec::new();
    for (i, first) in doc.sentences.iter().enumerate() {
        if !first.text.trim_end().ends_with('?') {
            continue;
        }
        if !paired {
            spans.push(Span { start: first.start, end: first.start + 1 });
            continue;
        }
        if let Some(second) = doc.sentences.get(i + 1) {
            if doc.section(first.start) == doc.section(second.start) && second.words <= rule.number("answer_max_words") && !second.text.trim_end().ends_with('?') {
                spans.push(Span { start: first.start, end: second.end });
            }
        }
    }
    let max = rule.number("max");
    let window = rule.number("window_words");
    clusters(doc, &spans.iter().map(|s| s.start).collect::<Vec<_>>(), max, window)
        .iter()
        .map(|group| {
            let last = *group.last().unwrap();
            let end = spans.iter().find(|s| s.start == last).unwrap().end;
            if paired {
                finding(group[max], end, format!("{} staged question-and-short-answer turns appear within {window} words.", group.len()), "Turn at least one question into a direct statement.")
            } else {
                finding(
                    group[max],
                    end,
                    format!("{} questions appear within {window} words; the passage is interrogating the reader instead of explaining.", group.len()),
                    "Keep the question that creates useful tension and state the others directly.",
                )
            }
        })
        .collect()
}

fn echoed(sentence: &Unit, doc: &Document, rule: &Resolved) -> Option<Finding> {
    let raw = doc.structural.slice(sentence.start, sentence.end);
    let pieces: Vec<String> = rx(r"\s*(?:,|;)\s*(?:(?:and|or)\s+)?").split(raw).map(normalize).filter(|p| word_count(p) >= 3).collect();
    let minimum = rule.number("minimum_clauses");
    if pieces.len() < minimum || pieces.len() > rule.number("maximum_clauses") {
        return None;
    }
    let mut prefixes: Vec<(String, usize)> = Vec::new();
    let mut suffixes: Vec<(String, usize)> = Vec::new();
    for piece in &pieces {
        let words: Vec<String> = rx(WORD).find_iter(piece).map(|m| m.as_str().to_lowercase()).collect();
        increment(&mut prefixes, words[..2].join(" "));
        increment(&mut suffixes, words[words.len() - 2..].join(" "));
    }
    let prefix = prefixes.iter().find(|(_, n)| *n >= minimum);
    let suffix = suffixes.iter().find(|(_, n)| *n >= minimum);
    let (repeated, _) = prefix.or(suffix)?;
    if rx(r"\d").is_match(repeated) {
        return None;
    }
    let position = if prefix.is_some() { "opening" } else { "ending" };
    Some(finding(
        sentence.start,
        sentence.end,
        format!("{} parallel clauses repeat the {position} '{repeated}'.", pieces.len()),
        "Keep the parallelism only if the rhythm earns its space; otherwise combine the clauses or vary the syntax.",
    ))
}

fn increment(groups: &mut Vec<(String, usize)>, key: String) {
    if let Some((_, count)) = groups.iter_mut().find(|(k, _)| k == &key) {
        *count += 1;
    } else {
        groups.push((key, 1));
    }
}

fn tricolons(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let pattern = insensitive(r":\s*[^,.;!?\n]{1,36},\s*[^,.;!?\n]{1,36},\s*(?:and|or)\s+[^.;!?\n]{1,48}");
    let mut spans: Vec<Span> = pattern.find_iter(&doc.structural.text).map(|m| doc.structural.span(m)).collect();
    for sentence in &doc.sentences {
        let raw = doc.structural.slice(sentence.start, sentence.end);
        if raw.matches(',').count() != 2 || !insensitive(r",\s*(?:and|or)\s+").is_match(raw) {
            continue;
        }
        let pieces: Vec<&str> = rx(r",\s*(?:and|or\s+)?|\s+(?:and|or)\s+").split(raw).filter(|s| !normalize(s).is_empty()).collect();
        if pieces.len() == 3 && pieces.iter().all(|s| (1..=8).contains(&word_count(s))) {
            spans.push(Span { start: sentence.start, end: sentence.end });
        }
    }
    spans.sort_by_key(|s| s.start);
    let max = rule.number("max");
    let window = rule.number("window_words");
    clusters(doc, &spans.iter().map(|s| s.start).collect::<Vec<_>>(), max, window)
        .iter()
        .map(|group| {
            finding(
                group[max],
                group.last().unwrap() + 1,
                format!("{} three-part rhetorical lists appear within {window} words.", group.len()),
                "Vary the list length or convert one list into a concrete example.",
            )
        })
        .collect()
}
