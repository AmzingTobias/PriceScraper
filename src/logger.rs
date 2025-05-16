use log::{Level, Log, Metadata, Record};
use std::io::{self, Write};

pub struct StdSplitLogger;

impl Log for StdSplitLogger {
    fn enabled(&self, metadata: &Metadata) -> bool {
        metadata.level() <= Level::Info
    }

    fn log(&self, record: &Record) {
        if self.enabled(record.metadata()) {
            let mut out: Box<dyn Write> = match record.level() {
                Level::Error | Level::Warn => Box::new(io::stderr()),
                _ => Box::new(io::stdout()),
            };

            let _ = writeln!(out, "{}: {}", record.level(), record.args());
        }
    }

    fn flush(&self) {}
}

pub static LOGGER: StdSplitLogger = StdSplitLogger;
