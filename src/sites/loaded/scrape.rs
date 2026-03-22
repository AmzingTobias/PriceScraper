use std::process::Command;
use std::time::SystemTime;

use scraper::{Html, Selector};

use crate::{PriceInfo, sites::Scraper};

use super::Loaded;

impl Scraper for Loaded {
    fn scrape(url: &str) -> Result<PriceInfo, String> {
        // 🔥 Call Playwright helper script
        let output = Command::new("node")
            .arg("/home/ubuntu/PriceScraper/playwright/fetch.js")
            .arg(url)
            .env("DISPLAY", ":99")
            .output()
            .map_err(|e| format!("Failed to run Playwright: {}", e))?;

        if !output.status.success() {
            return Err(format!(
                "Playwright exited with error: {}",
                String::from_utf8_lossy(&output.stderr)
            ));
        }

        let html_content = String::from_utf8(output.stdout)
            .map_err(|e| format!("Invalid UTF-8 from Playwright: {}", e))?;

        let document = Html::parse_document(&html_content);

        match is_product_in_stock(&document) {
            Ok(in_stock) => {
                if in_stock {
                    let selector = Selector::parse(r#"meta[property="product:price:amount"]"#)
                        .map_err(|e| format!("Meta HTML element could not be found: {}", e))?;

                    if let Some(element) = document.select(&selector).next() {
                        if let Some(price_str) = element.value().attr("content") {
                            match price_str.parse::<f64>() {
                                Ok(price) => {
                                    return Ok(PriceInfo {
                                        price,
                                        previous_price: None,
                                        timestamp: SystemTime::now(),
                                    });
                                }
                                Err(_) => return Err("Failed to parse price".to_string()),
                            }
                        } else {
                            return Err("Price attribute missing in meta tag".to_string());
                        }
                    }

                    Err(format!("Price could not be found in the HTML from {}", url))
                } else {
                    Err(format!("Product {url} out of stock"))
                }
            }
            Err(e) => Err(e),
        }
    }
}

fn is_product_in_stock(document: &Html) -> Result<bool, String> {
    let selector = Selector::parse("span").map_err(|e| format!("Selector parse error: {}", e))?;

    Ok(!document
        .select(&selector)
        .any(|element| element.text().collect::<String>().trim() == "Out of Stock"))
}
