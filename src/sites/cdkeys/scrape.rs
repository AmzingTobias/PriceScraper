use std::time::SystemTime;

use reqwest::{
    blocking::Client,
    header::{HeaderMap, USER_AGENT},
};
use scraper::{Html, Selector};

use crate::{PriceInfo, sites::Scraper};

use super::CDKeys;

impl Scraper for CDKeys {
    fn scrape(url: &str) -> Result<PriceInfo, String> {
        let mut headers = HeaderMap::new();
        headers.insert(
            USER_AGENT,
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
             (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
                .parse()
                .map_err(|e| format!("Header parse error: {}", e))?,
        );

        let client = Client::builder()
            .default_headers(headers)
            .build()
            .map_err(|e| format!("Client build error: {}", e))?;

        let response = client
            .get(url)
            .send()
            .map_err(|e| format!("Request error: {}", e))?;

        let html_content = response
            .text()
            .map_err(|e| format!("Error reading response text: {}", e))?;

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
                            return Err(format!("Price attribute missing in meta tag'",));
                        }
                    }
                    Err(format!("Price could not be found in the HTML from {}", url))
                } else {
                    Err(format!("Product {url} out of stock"))
                }
            }
            _ => Err(format!("Unable to determine stock for: {url}")),
        }
    }
}

fn is_product_in_stock(document: &Html) -> Result<bool, String> {
    let selector = Selector::parse("span").unwrap();

    // Iterate through all <span> elements and check their text
    Ok(document
        .select(&selector)
        .any(|element| element.text().collect::<String>().trim() == "Out of Stock")
        == false)
}
