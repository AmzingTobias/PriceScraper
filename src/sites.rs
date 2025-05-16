pub mod cdkeys;

use reqwest::Url;

use crate::PriceInfo;

pub struct Image {
    pub raw: Vec<u8>,
    pub extension: String,
}

pub struct GameImport {
    pub title: String,
    pub _edition: Option<String>,
    pub _platform: Option<String>,
    pub description: Option<String>,
    pub url: String,
    pub image: Option<Image>,
}

pub trait Scraper {
    fn scrape(url: &str) -> Result<PriceInfo, String>;
}

pub trait Importer {
    fn import(url: &str) -> Result<GameImport, String>;
}

pub fn scrape(url: &str) -> Result<PriceInfo, String> {
    let hostname = get_hostname(url);
    match hostname {
        Ok(host) if host == "www.cdkeys.com" => cdkeys::CDKeys::scrape(url),
        Ok(other) => Err(format!("Unsupported URL for scrape: {}", other)),
        Err(e) => Err(e),
    }
}

pub fn import(url: &str) -> Result<GameImport, String> {
    let hostname = get_hostname(url);
    match hostname {
        Ok(host) if host == "www.cdkeys.com" => cdkeys::CDKeys::import(url),
        Ok(other) => Err(format!("Unsupported URL for import: {}", other)),
        Err(e) => Err(e),
    }
}

fn get_hostname(url: &str) -> Result<String, String> {
    match Url::parse(url) {
        Ok(parsed_url) => {
            if let Some(host) = parsed_url.host_str() {
                Ok(String::from(host))
            } else {
                Err(String::from("No host found in URL"))
            }
        }
        Err(e) => Err(format!("Invalid URL: {}", e)),
    }
}
