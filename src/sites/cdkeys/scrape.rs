use std::time::SystemTime;

use regex::Regex;
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
                    let id_pattern = Regex::new(r"^product-price-\d+$")
                        .map_err(|e| format!("Regex compile error: {}", e))?;

                    let span_selector = Selector::parse("span")
                        .map_err(|e| format!("Span HTML element could not be found: {}", e))?;

                    for element in document.select(&span_selector) {
                        if let Some(id_value) = element.value().attr("id") {
                            if id_pattern.is_match(id_value) {
                                if let Some(price_str) = element.value().attr("data-price-amount") {
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
                                    return Err(format!(
                                        "Price attribute missing in span with id '{}'",
                                        id_value
                                    ));
                                }
                            }
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
    let stock_selector = Selector::parse(".product-usps-item.attribute.stock.unavailable")
        .map_err(|e| format!("Selector parse error: {}", e))?;

    let elements = document.select(&stock_selector);

    Ok(elements.count() == 0)
}
