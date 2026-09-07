mod cli;
mod config;
mod document;
mod markdown;
mod repetition;
mod rhetoric;
mod rules;
mod text;

fn main() {
    std::process::exit(cli::main());
}
