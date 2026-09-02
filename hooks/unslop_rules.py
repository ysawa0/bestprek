"""Unslop rule catalog."""

from .unslop_checks import (
    bold_density,
    chatbot_residue,
    echoed_clauses,
    em_dash_density,
    heading_density,
    loaded_word_repetition,
    negative_parallelism,
    no_chain,
    paragraph_openers,
    parenthetical_density,
    phrase_checker,
    question_answer,
    question_density,
    sentence_openers,
    short_sentence_run,
    transition_repetition,
    tricolon_density,
    uniform_sentence_length,
)
from .unslop_core import Rule

RULES = [
    Rule(
        "artifact.chatbot-residue",
        "Generated-chat or citation artifacts left in prose",
        "error",
        chatbot_residue,
    ),
    Rule(
        "verbosity.throat-clearing",
        "Generic opening clauses that delay the actual claim",
        "warning",
        phrase_checker(
            [
                (
                    r"\bwhen it comes to\b",
                    "'When it comes to' delays the subject.",
                    "Start with the subject and verb.",
                ),
                (
                    r"\bin (?:today's|the modern|an? ever-changing|an? ever-evolving) (?:world|era|landscape)\b",
                    "A generic era or landscape opener adds atmosphere instead of information.",
                    "Name the specific change, market, or constraint.",
                ),
                (
                    r"\bin the (?:realm|world) of\b",
                    "This realm/world framing is vague throat-clearing.",
                    "Name the field directly.",
                ),
                (
                    r"\bat its core\b",
                    "'At its core' often announces a simplification instead of making it.",
                    "State the simplified claim directly.",
                ),
                (
                    r"\bthe fact of the matter is\b",
                    "This lead-in delays the claim.",
                    "Delete the lead-in.",
                ),
            ]
        ),
    ),
    Rule(
        "verbosity.filler",
        "Wordy phrases with shorter direct equivalents",
        "warning",
        phrase_checker(
            [
                (
                    r"\bin order to\b",
                    "'In order to' is usually just 'to'.",
                    "Replace it with 'to'.",
                ),
                (
                    r"\bdue to the fact that\b",
                    "This phrase is wordier than 'because'.",
                    "Replace it with 'because'.",
                ),
                (
                    r"\bat this point in time\b",
                    "This phrase is usually just 'now'.",
                    "Replace it with 'now'.",
                ),
                (
                    r"\bhas the ability to\b|\bis able to\b",
                    "This ability phrase usually hides a direct verb.",
                    "Use 'can' or the direct verb.",
                ),
                (
                    r"\ba wide variety of\b",
                    "This quantity phrase is vague unless the variety matters.",
                    "Use 'many', list examples, or quantify.",
                ),
            ]
        ),
    ),
    Rule(
        "verbosity.redundant-pair",
        "Redundant or doubled expressions",
        "warning",
        phrase_checker(
            [
                (
                    r"\beach and every\b",
                    "'Each and every' repeats the same idea.",
                    "Choose 'each' or 'every'.",
                ),
                (
                    r"\bvarious different\b",
                    "'Various different' is redundant.",
                    "Choose 'various' or 'different'.",
                ),
                (
                    r"\bpast history\b",
                    "History is already in the past.",
                    "Use 'history'.",
                ),
                (
                    r"\bfuture plans\b",
                    "Plans normally concern the future.",
                    "Use 'plans' unless contrasting with past plans.",
                ),
                (
                    r"\bcompletely eliminate\b",
                    "'Eliminate' already means remove completely.",
                    "Use 'eliminate'.",
                ),
            ]
        ),
    ),
    Rule(
        "phrase.note-to-reader",
        "Meta-language that tells the reader what to notice",
        "info",
        phrase_checker(
            [
                (
                    r"\bit (?:is|'s) important to note that\b",
                    "The sentence tells the reader what to note instead of proving its importance.",
                    "Delete the lead-in and strengthen the claim.",
                ),
                (
                    r"\bit (?:is|'s) worth noting that\b|\bit should be noted that\b",
                    "The note-to-reader phrase adds editorial scaffolding.",
                    "State the point directly.",
                ),
                (
                    r"\bthe key takeaway is\b",
                    "This phrase often repeats a point the paragraph should already establish.",
                    "State the takeaway once, in the strongest location.",
                ),
            ]
        ),
        strict_severity="warning",
    ),
    Rule(
        "phrase.marketing-language",
        "Generic promotional wording without a concrete property",
        "info",
        phrase_checker(
            [
                (
                    r"\bunlock(?:s|ed|ing)? (?:the )?(?:power|potential|possibilities)\b",
                    "'Unlocking potential' is promotional unless the mechanism is named.",
                    "Describe the capability or measured result.",
                ),
                (
                    r"\bseamless(?:ly)?\b",
                    "'Seamless' makes a quality claim without naming the seam.",
                    "Name the transition, integration, or failure mode.",
                ),
                (
                    r"\bgame[- ]changer\b",
                    "'Game-changer' substitutes enthusiasm for evidence.",
                    "Describe what changed and by how much.",
                ),
                (
                    r"\belevat(?:e|es|ed|ing) (?:your|the)\b",
                    "'Elevate' is generic promotional language here.",
                    "Use the concrete improvement.",
                ),
                (
                    r"\btransformative\b",
                    "'Transformative' needs a specific before-and-after claim.",
                    "Describe the transformation.",
                ),
                (
                    r"\bultimate guide\b",
                    "'Ultimate guide' makes a completeness claim the article is unlikely to prove.",
                    "Use a descriptive title that states the scope.",
                ),
            ]
        ),
        strict_severity="warning",
    ),
    Rule(
        "phrase.abstract-role",
        "Abstract role language that can usually be replaced by a direct verb",
        "info",
        phrase_checker(
            [
                (
                    r"\bserves as (?:a|an|the)\b",
                    "'Serves as' often hides a simpler verb.",
                    "Use 'is', 'provides', or the specific action.",
                ),
                (
                    r"\bplays? (?:a )?(?:pivotal|crucial|vital|important) role\b",
                    "The sentence announces importance without demonstrating it.",
                    "Name the consequence or dependency.",
                ),
                (
                    r"\bstands as (?:a|an|the)\b",
                    "'Stands as' adds ceremony to a direct claim.",
                    "Use 'is' or a more specific verb.",
                ),
            ]
        ),
        strict_severity="warning",
    ),
    Rule(
        "phrase.landscape",
        "Vague landscape or tapestry metaphors",
        "warning",
        phrase_checker(
            [
                (
                    r"\bever[- ]evolving(?:\s+[A-Za-z-]+){0,2}\s+landscape\b",
                    "'Ever-evolving landscape' is vague and overworked.",
                    "Name what changed and when.",
                ),
                (
                    r"\bin today['’]s(?:\s+[A-Za-z-]+){0,2}\s+landscape\b",
                    "This landscape frame is generic.",
                    "Name the current condition and its consequence.",
                ),
                (
                    r"\b(?:rich|complex|intricate) tapestry\b",
                    "The tapestry metaphor decorates the claim without clarifying it.",
                    "Describe the actual components or relationship.",
                ),
            ]
        ),
    ),
    Rule(
        "phrase.vague-attribution",
        "Claims attributed to unnamed authorities",
        "warning",
        phrase_checker(
            [
                (
                    r"\bexperts (?:say|argue|believe|agree)\b",
                    "'Experts' is too vague to support the claim.",
                    "Name the expert, institution, or source.",
                ),
                (
                    r"\bstudies (?:show|suggest|indicate|have shown)\b",
                    "'Studies' needs a citation or identifying detail.",
                    "Cite the study or state what evidence you reviewed.",
                ),
                (
                    r"\bit is widely (?:believed|known|accepted)\b",
                    "A claim of broad agreement needs evidence.",
                    "Name the source of the consensus or remove the appeal to consensus.",
                ),
            ]
        ),
    ),
    Rule(
        "rhetoric.negative-parallelism",
        "Repeated contrast reframes",
        "warning",
        negative_parallelism,
        {"max": 1, "window_words": 500},
        strict_defaults={"max": 0},
    ),
    Rule(
        "rhetoric.no-chain",
        "Three or more 'no X, no Y' items",
        "warning",
        no_chain,
        {"minimum_items": 3},
        strict_defaults={"minimum_items": 2},
    ),
    Rule(
        "rhetoric.question-answer",
        "Repeated staged questions followed by short answers",
        "warning",
        question_answer,
        {"max": 1, "window_words": 400, "answer_max_words": 5},
        strict_defaults={"max": 0},
    ),
    Rule(
        "rhetoric.question-density",
        "Too many questions in a short passage",
        "warning",
        question_density,
        {"max": 3, "window_words": 500},
        strict_defaults={"max": 2},
    ),
    Rule(
        "rhetoric.echoed-clauses",
        "Parallel clauses repeat the same opening or ending",
        "warning",
        echoed_clauses,
        {"minimum_clauses": 3, "maximum_clauses": 5},
    ),
    Rule(
        "rhetoric.tricolon-density",
        "Repeated three-part rhetorical lists",
        "info",
        tricolon_density,
        {"max": 3, "window_words": 750},
        strict_severity="warning",
        strict_defaults={"max": 2},
    ),
    Rule(
        "repetition.sentence-opener",
        "Repeated sentence openings",
        "warning",
        sentence_openers,
        {"consecutive": 3, "window_sentences": 8, "window_count": 5},
        strict_defaults={"window_count": 4},
    ),
    Rule(
        "repetition.paragraph-opener",
        "Repeated paragraph openings",
        "warning",
        paragraph_openers,
        {"consecutive": 3, "window_paragraphs": 6, "window_count": 4},
        strict_defaults={"window_count": 3},
    ),
    Rule(
        "repetition.transition",
        "Repeated stock transitions",
        "warning",
        transition_repetition,
        {"max": 2, "window_words": 500},
        strict_defaults={"max": 1},
    ),
    Rule(
        "repetition.loaded-word",
        "Repeated abstract or promotional vocabulary",
        "warning",
        loaded_word_repetition,
        {"max": 2, "window_words": 500},
        strict_defaults={"max": 1},
    ),
    Rule(
        "rhythm.short-sentence-run",
        "Run of very short sentences",
        "warning",
        short_sentence_run,
        {"max_words": 5, "minimum_run": 3},
        strict_defaults={"max_words": 6},
    ),
    Rule(
        "rhythm.uniform-sentence-length",
        "Unusually uniform sentence lengths",
        "off",
        uniform_sentence_length,
        {"minimum_sentences": 10, "maximum_cv": 0.18},
        strict_severity="info",
    ),
    Rule(
        "density.em-dash",
        "High em-dash density",
        "warning",
        em_dash_density,
        {"max": 4, "window_words": 500},
        strict_defaults={"max": 3},
    ),
    Rule(
        "density.bold",
        "High bold-emphasis density",
        "warning",
        bold_density,
        {"max": 10, "window_words": 500},
        strict_defaults={"max": 6},
    ),
    Rule(
        "density.parenthetical",
        "High parenthetical-aside density",
        "off",
        parenthetical_density,
        {"max": 6, "window_words": 500},
        strict_severity="info",
        strict_defaults={"max": 5},
    ),
    Rule(
        "structure.heading-density",
        "Many headings relative to prose",
        "off",
        heading_density,
        {"minimum_headings": 6, "min_words_per_heading": 70},
        strict_severity="info",
    ),
]
RULES_BY_ID = {rule.id: rule for rule in RULES}
