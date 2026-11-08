use crate::config::Resolved;
use crate::document::Document;
use crate::text::{insensitive, Span};

#[derive(Clone)]
pub struct Finding {
    pub start: usize,
    pub end: usize,
    pub message: String,
    pub suggestion: Option<String>,
}
pub fn finding(start: usize, end: usize, message: impl Into<String>, suggestion: &str) -> Finding {
    Finding {
        start,
        end,
        message: message.into(),
        suggestion: Some(suggestion.to_owned()),
    }
}

pub fn clusters(doc: &Document, offsets: &[usize], max: usize, window: usize) -> Vec<Vec<usize>> {
    if offsets.len() <= max {
        return Vec::new();
    }
    let mut ordered = offsets.to_vec();
    ordered.sort_unstable();
    ordered.dedup();
    let indices: Vec<usize> = ordered.iter().map(|&p| doc.word_index(p)).collect();
    let mut result = Vec::new();
    let mut left = 0;
    let mut right = 0;
    while right < ordered.len() {
        while left < right && indices[right] - indices[left] > window {
            left += 1;
        }
        if right - left + 1 > max {
            let mut cursor = right + 1;
            while cursor < ordered.len() && indices[cursor] - indices[left] <= window {
                cursor += 1;
            }
            result.push(ordered[left..cursor].to_vec());
            right = cursor;
            left = right;
        } else {
            right += 1;
        }
    }
    result
}

pub fn check(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    match rule.rule.checker.as_str() {
        "check" => phrases(doc, rule),
        "chatbot_residue" => residue(doc),
        "negative_parallelism" => negative(doc, rule),
        "no_chain" => no_chain(doc, rule),
        "question_answer" | "question_density" | "echoed_clauses" | "tricolon_density" => crate::rhetoric::check(doc, rule),
        "sentence_openers" | "paragraph_openers" | "transition_repetition" | "loaded_word_repetition" | "short_sentence_run" | "uniform_sentence_length" => crate::repetition::check(doc, rule),
        "heading_density" => headings(doc, rule),
        "em_dash_density" => density(
            doc,
            rule,
            doc.visible.chars.iter().enumerate().filter(|(_, &c)| c == '—').map(|(i, _)| i).collect(),
            "em dashes",
            "Keep the strongest interruption and use commas, parentheses, or separate sentences elsewhere.",
        ),
        "bold_density" => density(doc, rule, doc.bold.iter().map(|s| s.start).collect(), "bold spans", "Use emphasis only where the reader genuinely needs a visual anchor."),
        "parenthetical_density" => density(doc, rule, doc.parenthetical.iter().map(|s| s.start).collect(), "parenthetical asides", "Move necessary context into the sentence and delete dispensable asides."),
        name => panic!("Unknown checker {name}"),
    }
}

fn phrases(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let mut candidates = Vec::new();
    for (pattern, phrase) in rule.patterns.iter().zip(&rule.rule.phrases) {
        for m in pattern.find_iter(&doc.visible.text) {
            let span = doc.visible.span(m);
            candidates.push(Finding {
                start: span.start,
                end: span.end,
                message: phrase.message.clone(),
                suggestion: phrase.suggestion.clone(),
            });
        }
    }
    candidates.sort_by_key(|f| (f.start, std::cmp::Reverse(f.end - f.start)));
    let mut result: Vec<Finding> = Vec::new();
    for candidate in candidates {
        if result.last().is_some_and(|prev| candidate.start < prev.end) {
            continue;
        }
        result.push(candidate);
    }
    result
}

fn residue(doc: &Document) -> Vec<Finding> {
    let pattern = insensitive(concat!(
        r"\bas an AI(?: language)? model\b|\bknowledge cutoff\b|\bas of my last (?:update|training)\b|",
        r"\bI (?:cannot|can't|do not|don't) (?:browse the internet|access real[- ]time)\b|",
        r"\boaicite\b|\bcontentReference\b|\battributableIndex\b|\bturn\d+(?:search|news|image|view)\d+\b|",
        r"[?&]utm_source=(?:chatgpt|openai)\b"
    ));
    pattern
        .find_iter(&doc.visible.text)
        .map(|m| {
            let s = doc.visible.span(m);
            finding(s.start, s.end, "Chatbot or generated-citation residue remains in the prose.", "Remove the artifact and verify the surrounding claim.")
        })
        .collect()
}

fn negative(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let mut spans = Vec::new();
    for pattern in [
        r"\b(?:this|that|it|[A-Z][A-Za-z0-9' -]{0,35})\s+(?:isn't|is not|wasn't|was not)\s+(?:just\s+)?[^.!?\n]{2,100}[.!?]\s+(?:it(?:'s| is| was)|this is|that(?:'s| is))\s+[^.!?\n]{2,120}",
        r"\bnot\s+(?:just\s+)?[^,.;!?\n]{2,80},?\s+(?:but|rather)\s+[^.;!?\n]{2,110}",
    ] {
        spans.extend(insensitive(pattern).find_iter(&doc.visible.text).map(|m| doc.visible.span(m)));
    }
    spans.sort_by_key(|s| (s.start, std::cmp::Reverse(s.end - s.start)));
    let mut unique: Vec<Span> = Vec::new();
    for s in spans {
        if !unique.last().is_some_and(|p| s.start < p.end) {
            unique.push(s);
        }
    }
    let max = rule.number("max");
    let window = rule.number("window_words");
    clusters(doc, &unique.iter().map(|s| s.start).collect::<Vec<_>>(), max, window)
        .iter()
        .map(|group| {
            let last = *group.last().unwrap();
            let end = unique.iter().find(|s| s.start == last).unwrap().end;
            finding(
                group[max],
                end,
                format!("{} contrast reframes appear within {window} words; repeated 'not X, but Y' structure starts to sound manufactured.", group.len()),
                "State at least one positive claim directly, or keep only the strongest contrast.",
            )
        })
        .collect()
}

fn no_chain(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let pattern = insensitive(r"\bno\s+[^,.;:!?\n]{1,45}(?:\s*,\s*no\s+[^,.;:!?\n]{1,45})+");
    let mut result = Vec::new();
    for m in pattern.find_iter(&doc.visible.text) {
        let count = insensitive(r"\bno\s+").find_iter(m.as_str()).count();
        if count < rule.number("minimum_items") {
            continue;
        }
        let s = doc.visible.span(m);
        result.push(finding(s.start, s.end, format!("A {count}-item 'no X, no Y' chain performs emphasis without adding evidence."), "Replace the chain with the specific positive claim."));
    }
    result
}

fn density(doc: &Document, rule: &Resolved, offsets: Vec<usize>, noun: &str, suggestion: &str) -> Vec<Finding> {
    let max = rule.number("max");
    let window = rule.number("window_words");
    clusters(doc, &offsets, max, window)
        .iter()
        .map(|group| finding(group[max], group.last().unwrap() + 1, format!("{} {noun} appear within {window} words.", group.len()), suggestion))
        .collect()
}

fn headings(doc: &Document, rule: &Resolved) -> Vec<Finding> {
    let count = doc.headings.len();
    if count < rule.number("minimum_headings") || doc.word_starts.is_empty() {
        return Vec::new();
    }
    let ratio = doc.word_starts.len() as f64 / count as f64;
    if ratio >= rule.number("min_words_per_heading") as f64 {
        return Vec::new();
    }
    vec![finding(
        doc.headings[usize::from(count > 1)].start,
        doc.headings.last().unwrap().end,
        format!("{count} headings divide {} words, or only {ratio:.0} words per heading.", doc.word_starts.len()),
        "Merge sections whose headings promise more structure than the content delivers.",
    )]
}
