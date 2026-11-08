use crate::text::insensitive;
use regex::Regex;
use serde::Deserialize;
use serde_json::{Map, Value};
use std::collections::BTreeMap;
use std::sync::Arc;

#[derive(Deserialize)]
pub struct Phrase {
    pub pattern: String,
    pub message: String,
    pub suggestion: Option<String>,
}
#[derive(Deserialize)]
pub struct Rule {
    pub id: String,
    pub summary: String,
    pub recommended_severity: String,
    pub strict_severity: Option<String>,
    pub defaults: BTreeMap<String, Value>,
    pub strict_defaults: BTreeMap<String, Value>,
    pub checker: String,
    pub phrases: Vec<Phrase>,
}
pub struct Resolved {
    pub rule: Rule,
    pub severity: String,
    pub options: BTreeMap<String, Value>,
    pub patterns: Vec<Arc<Regex>>,
}
impl Resolved {
    pub fn number(&self, name: &str) -> usize {
        self.options[name].as_u64().unwrap() as usize
    }
    pub fn float(&self, name: &str) -> f64 {
        self.options[name].as_f64().unwrap()
    }
}

pub fn catalogue() -> Vec<Rule> {
    serde_json::from_str(include_str!("rules.json")).unwrap()
}
pub fn severity(level: &str) -> i8 {
    match level {
        "off" => -1,
        "info" => 0,
        "warning" => 1,
        "error" => 2,
        _ => -2,
    }
}

pub fn read_config(path: Option<&str>) -> Result<Map<String, Value>, String> {
    let default;
    let path = match path {
        Some(path) => path,
        None => {
            default = std::env::current_dir().map_err(|e| e.to_string())?.join(".unslop.json");
            if !default.is_file() {
                return Ok(Map::new());
            }
            default.to_str().ok_or("Invalid config path")?
        }
    };
    let text = std::fs::read_to_string(path).map_err(|e| format!("Cannot read config {path}: {e}"))?;
    let value: Value = serde_json::from_str(&text).map_err(|e| format!("Cannot read config {path}: {e}"))?;
    let data = value.as_object().ok_or("Config root must be a JSON object")?.clone();
    let unknown: Vec<&str> = data.keys().map(String::as_str).filter(|k| !["preset", "fail_level", "rules"].contains(k)).collect();
    if !unknown.is_empty() {
        return Err(format!("Unknown config keys: {}", unknown.join(", ")));
    }
    for (name, allowed, message) in [
        ("preset", vec!["recommended", "strict"], "'preset' must be 'recommended' or 'strict'"),
        ("fail_level", vec!["info", "warning", "error", "none"], "'fail_level' must be info, warning, error, or none"),
    ] {
        if let Some(value) = data.get(name).filter(|v| !v.is_null()) {
            if !value.as_str().is_some_and(|s| allowed.contains(&s)) {
                return Err(message.to_owned());
            }
        }
    }
    if let Some(rules) = data.get("rules") {
        let rules = rules.as_object().ok_or("'rules' must be a JSON object")?;
        let known = catalogue();
        let unknown: Vec<&str> = rules.keys().map(String::as_str).filter(|id| !known.iter().any(|r| r.id == *id)).collect();
        if !unknown.is_empty() {
            return Err(format!("Unknown rules: {}", unknown.join(", ")));
        }
    }
    Ok(data)
}

pub fn resolve(preset: &str, config: &Map<String, Value>) -> Result<Vec<Resolved>, String> {
    let mut resolved = Vec::new();
    for rule in catalogue() {
        let mut level = rule.recommended_severity.clone();
        let mut options = rule.defaults.clone();
        if preset == "strict" {
            level = rule.strict_severity.as_ref().unwrap_or(&level).clone();
            options.extend(rule.strict_defaults.clone());
        }
        if let Some(value) = config.get("rules").and_then(|v| v.get(&rule.id)).filter(|v| !v.is_null()) {
            if let Some(s) = value.as_str() {
                level = s.to_owned();
            } else if let Some(object) = value.as_object() {
                if let Some(v) = object.get("severity") {
                    level = v.as_str().unwrap_or("").to_owned();
                }
                let unknown: Vec<&str> = object.keys().map(String::as_str).filter(|&k| k != "severity" && !rule.defaults.contains_key(k) && !rule.strict_defaults.contains_key(k)).collect();
                if !unknown.is_empty() {
                    return Err(format!("Rule '{}' has unknown options: {}", rule.id, unknown.join(", ")));
                }
                options.extend(object.iter().filter(|(k, _)| *k != "severity").map(|(k, v)| (k.clone(), v.clone())));
            } else {
                return Err(format!("Rule '{}' must be a severity string or JSON object", rule.id));
            }
        }
        if severity(&level) < -1 {
            return Err(format!("Rule '{}' has invalid severity '{}'", rule.id, level));
        }
        for (name, value) in &options {
            let prefix = format!("Rule '{}' option '{}'", rule.id, name);
            if name == "maximum_cv" {
                if !value.as_f64().is_some_and(|n| n > 0.0) {
                    return Err(format!("{prefix} must be a positive number"));
                }
                continue;
            }
            let n = value.as_i64().ok_or_else(|| format!("{prefix} must be an integer"))?;
            if n < if name == "max" { 0 } else { 1 } {
                return Err(format!("{prefix} has an invalid range"));
            }
        }
        if options.get("minimum_clauses").and_then(Value::as_i64) > options.get("maximum_clauses").and_then(Value::as_i64) {
            return Err(format!("Rule '{}' requires minimum_clauses <= maximum_clauses", rule.id));
        }
        let patterns = rule.phrases.iter().map(|p| insensitive(&p.pattern)).collect();
        resolved.push(Resolved { rule, severity: level, options, patterns });
    }
    Ok(resolved)
}
