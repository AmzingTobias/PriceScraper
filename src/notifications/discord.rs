use discord_webhook_rs::{Embed, Error, Footer, Webhook};

use super::Notifications;
use crate::{PriceInfo, db::db::Sources};

pub fn send_webhook(
    webhook_url: &str,
    source: &Sources,
    notification_type: &Notifications,
    price_info: &PriceInfo,
    historical_low_price: &Option<PriceInfo>,
    image_web_path: &String,
    image_file_name: &Option<String>,
) -> Result<(), Error> {
    log::info!("Sending Webhook");
    let webhook = Webhook::new(webhook_url).content("");
    let embed = Embed::new()
        .title(source.product_name.clone())
        .description(get_description(notification_type, price_info))
        .url(source.site_link.clone())
        .color(get_webhook_colour(notification_type))
        .footer(Footer::new().text(set_historical_low_footer(price_info, historical_low_price)));

    match image_file_name {
        Some(image_file_name) => {
            let embed = embed.image(format!("{}/{}", image_web_path, image_file_name));
            webhook.add_embed(embed).send()?
        }
        None => webhook.add_embed(embed).send()?,
    };
    Ok(())
}

fn get_description(notification_type: &Notifications, price_info: &PriceInfo) -> String {
    match notification_type {
        Notifications::PriceHasDecreased
        | Notifications::PriceHasIncreased
        | Notifications::HistoricalLow => {
            let difference_type = match notification_type {
                Notifications::PriceHasDecreased => "**PRICE DECREASED**",
                Notifications::HistoricalLow => "**NEW HISTORICAL LOW**",
                _ => "**PRICE INCREASED**",
            };

            if let Some(old_price) = price_info.previous_price {
                format!(
                    "{}\n**£{:.2}** changed from £{:.2} | {:.2}%",
                    difference_type,
                    price_info.price,
                    old_price,
                    get_difference_as_percentage(price_info.price, old_price)
                )
            } else {
                format!(
                    "**PRICE {}**\n**£{:.2}**",
                    difference_type, price_info.price
                )
            }
        }
        Notifications::FirstPrice => format!("**PRICE FOUND**\n£{:.2}", price_info.price),
        Notifications::_Error | Notifications::None => String::from(""),
    }
}

fn set_historical_low_footer(
    current_price: &PriceInfo,
    historical_low_price: &Option<PriceInfo>,
) -> String {
    if let Some(historical_low_price) = historical_low_price {
        let datetime: chrono::DateTime<chrono::Local> = historical_low_price.timestamp.into();
        // Format the date as DD-MM-YYYY
        let formatted_date = datetime.format("%d-%m-%Y").to_string();
        format!(
            "Historical low: £{:.2}, which occurred on: {} Difference of: £{:.2}",
            historical_low_price.price,
            formatted_date,
            historical_low_price.price - current_price.price
        )
    } else {
        format!("")
    }
}

fn get_webhook_colour(notification_type: &Notifications) -> u32 {
    match notification_type {
        Notifications::None => u32::from_str_radix("FFFFFF", 16).unwrap(),
        Notifications::PriceHasDecreased | Notifications::HistoricalLow => {
            u32::from_str_radix("77dd77", 16).unwrap()
        }
        Notifications::PriceHasIncreased => u32::from_str_radix("dd7777", 16).unwrap(),
        Notifications::FirstPrice => u32::from_str_radix("dddd77", 16).unwrap(),
        Notifications::_Error => u32::from_str_radix("865AB3", 16).unwrap(),
    }
}

fn get_difference_as_percentage(new_price: f64, old_price: f64) -> f64 {
    let difference = (old_price - new_price) / old_price;
    if difference.is_nan() || difference.is_infinite() {
        return 100.0;
    } else {
        let percentage = difference * 100.0;
        if new_price >= old_price {
            percentage * -1.0
        } else {
            percentage
        }
    }
}
