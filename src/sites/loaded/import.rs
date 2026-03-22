use std::process::Command;

use reqwest::{
    blocking::Client,
    header::{HeaderMap, USER_AGENT},
};
use scraper::{Html, Selector};

use crate::sites::{GameImport, Image, Importer};

use super::Loaded;

impl Importer for Loaded {
    fn import(url: &str) -> Result<GameImport, String> {
        let document = get_html_document(url)?;

        let image_src = get_image_src(&document);
        let image: Option<Image> = match image_src {
            Some(image_src) => {
                let image = download_image(image_src);
                match image {
                    Ok(res) => Some(res),
                    Err(err) => {
                        log::warn!("Error downloading image: {:?}", err);
                        None
                    }
                }
            }
            None => None,
        };

        return Ok(GameImport {
            title: get_title(&document)?,
            description: match get_description(&document) {
                Ok(description) => Some(description),
                Err(err) => {
                    log::warn!("Error getting product description: {}", err);
                    None
                }
            },
            _edition: get_edition(&document),
            _platform: get_platform(&document),
            url: String::from(url),
            image,
        });
    }
}

fn get_html_document(url: &str) -> Result<Html, String> {
    let output = Command::new("node")
        .arg("/home/ubuntu/PriceScraper/playwright/fetch.js")
        .arg(url)
        .env("DISPLAY", ":99")
        .output()
        .expect("Failed to run Playwright");

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }

    let html_content = String::from_utf8(output.stdout)
        .map_err(|e| format!("Invalid UTF-8 from Playwright: {}", e))?;

    Ok(Html::parse_document(&html_content))
}
