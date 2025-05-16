use reqwest::{
    blocking::Client,
    header::{HeaderMap, USER_AGENT},
};
use scraper::{Html, Selector};

use crate::sites::{GameImport, Image, Importer};

use super::CDKeys;

impl Importer for CDKeys {
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

    Ok(Html::parse_document(&html_content))
}

fn get_title(document: &Html) -> Result<String, String> {
    let page_title_selector =
        Selector::parse(".page-title").map_err(|e| format!("Selector parse error: {}", e))?;

    let mut elements = document.select(&page_title_selector);

    let element = elements
        .next()
        .ok_or_else(|| "No element with class 'page-title' found".to_string())?;

    let title = element
        .value()
        .attr("data-text")
        .ok_or_else(|| "Attribute 'data-text' not found".to_string())?;

    Ok(title.to_string())
}

fn get_description(document: &Html) -> Result<String, String> {
    let description_selector =
        Selector::parse(".description").map_err(|e| format!("Selector parse error: {}", e))?;

    if let Some(div_element) = document.select(&description_selector).next() {
        let p_selector =
            Selector::parse("p").map_err(|e| format!("Selector parse error for <p>: {}", e))?;

        let mut paragraphs: Vec<String> = div_element
            .select(&p_selector)
            .map(|p| p.text().collect::<Vec<_>>().join(" "))
            .collect();

        if paragraphs.is_empty() {
            Err("No <p> elements found in target div.".to_string())
        } else {
            // Remove "Read More" text
            paragraphs.pop();
            let paragraphs = paragraphs.join("\n");
            Ok(paragraphs)
        }
    } else {
        Err("Target div not found.".to_string())
    }
}

fn get_edition(document: &Html) -> Option<String> {
    // Select the div with the specified class
    let div_selector =
        Selector::parse(&format!("div.{}", "product-info-selection_editions")).ok()?;
    let select_selector = Selector::parse("select").ok()?;
    let option_selector = Selector::parse("option").ok()?;

    // Find the first div with the class
    let div = document.select(&div_selector).next()?;
    // Find the select inside that div
    let select = div.select(&select_selector).next()?;

    // Find the selected option (with the "selected" attribute)
    for option in select.select(&option_selector) {
        let el = option.value();
        if el.attr("selected").is_some() {
            return Some(option.text().collect::<Vec<_>>().join(" "));
        }
    }

    // If no option has "selected", return the first one if available
    select
        .select(&option_selector)
        .next()
        .and_then(|o| Some(o.text().collect::<Vec<_>>().join(" ").trim().to_string()))
}

fn get_platform(document: &Html) -> Option<String> {
    // Using the full class value for specificity
    let selector =
        Selector::parse("div.product.attribute-icon.attribute.platforms .value").unwrap();

    // Try to extract the platform (inner text) and return it
    for element in document.select(&selector) {
        let platform = element
            .text()
            .collect::<Vec<_>>()
            .join("")
            .trim()
            .to_string();
        return Some(platform); // Return the extracted platform
    }

    None // If no platform is found, return None
}

fn get_image_src(document: &Html) -> Option<String> {
    let selector = Selector::parse("img.gallery-placeholder__image").unwrap();

    // Try to extract the platform (inner text) and return it
    for element in document.select(&selector) {
        let image = element.value().attr("src");
        return match image {
            Some(src) => Some(src.to_string()),
            None => None,
        };
    }

    None // If no platform is found, return None
}

fn download_image(image_src: String) -> Result<Image, String> {
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
        .get(&image_src)
        .send()
        .map_err(|e| format!("Request error: {}", e))?;

    // Check if the request was successful
    if response.status().is_success() {
        // Write the image bytes to the file
        let content = response
            .bytes()
            .map_err(|e| format!("Failed to convert to bytes: {}", e))?
            .to_vec();
        if let Some(kind) = infer::get(&content) {
            let extension = kind.extension();
            let allowed_extensions = ["png", "jpeg", "jpg"];
            if allowed_extensions.contains(&extension) {
                Ok(Image {
                    raw: content,
                    extension: extension.to_owned(),
                })
            } else {
                Err(format!("File type not allowed"))
            }
        } else {
            Err(format!("Unknown file type downloaded"))
        }
    } else {
        Err(format!(
            "Response failed with status code: {}",
            response.status()
        ))
    }
}
