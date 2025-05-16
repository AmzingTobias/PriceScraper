use std::fs;
use std::time::SystemTime;
use std::{env, path::PathBuf};

use db::db::{
    Sources, add_game, add_new_price, get_historical_low_for_product, get_image_for_product,
    get_webhooks_for_notify,
};
mod logger;
use notifications::discord;
use rusqlite::Connection;
mod db;
mod notifications;
mod sites;
struct PriceInfo {
    price: f64,
    previous_price: Option<f64>,
    timestamp: SystemTime,
}

#[derive(serde::Deserialize)]
struct Config {
    pub image_save_path: PathBuf,
    pub delay_between_scrape_seconds: u64,
    pub web_server_path_for_images: String,
    pub database_path: String,
}

fn load_config() -> Config {
    let default_config = Config {
        image_save_path: std::env::current_dir().expect("Default config cannot be used"),
        delay_between_scrape_seconds: 2,
        web_server_path_for_images: String::from(""),
        database_path: String::from("prices.db"),
    };

    let config_path = env::var("PRICESCRAPER_CONFIG_PATH");
    match config_path {
        Ok(config_path) => {
            let config_data = fs::read_to_string(&config_path).expect("Failed to read config file");
            let config: Config =
                serde_json::from_str(&config_data).expect("Config file cannot be parsed");
            config
        }
        Err(_) => {
            log::warn!("Config value not set, using default config");
            default_config
        }
    }
}

fn main() {
    log::set_logger(&logger::LOGGER)
        .map(|()| log::set_max_level(log::LevelFilter::Trace))
        .expect("Failed to initialize logger");

    let config = load_config();

    let args: Vec<String> = env::args().collect();
    let mut conn = Connection::open(&config.database_path).unwrap();

    match db::db::init_db(&mut conn) {
        Ok(()) => {
            let mode = &args.get(1);
            if let Some(mode) = mode {
                match mode.as_str() {
                    "scrape" => {
                        scrape_all_sources(&mut conn, &config);
                    }
                    "import" => {
                        let import_result = import_from_argumnet(&mut conn, &args, &config);
                        let _ = import_result.inspect_err(|err| {
                            log::error!("{err}");
                        });
                    }
                    _ => log::error!("Mode supplied is not supported: {}", mode),
                }
            } else {
                // No mode selected, scrape by default
                log::info!("No mode selected, scraping by default");
                scrape_all_sources(&mut conn, &config);
            }
        }
        Err(err) => {
            log::error!("{err}");
        }
    }
}

fn scrape_all_sources(conn: &mut Connection, config: &Config) {
    let sources = db::db::get_sources(&conn);
    if let Ok(sources) = sources {
        sources.iter().for_each(|source| {
            let scrape_result = scrape_source(conn, source, config);
            std::thread::sleep(std::time::Duration::from_secs(
                config.delay_between_scrape_seconds,
            ));
            if let Err(err) = scrape_result {
                log::warn!(
                    "Scrape failed on product: {} with error: {}",
                    source.product_id,
                    err
                );
            }
        })
    }
    log::info!("Scrape finished");
}

fn scrape_source(conn: &mut Connection, source: &Sources, config: &Config) -> Result<(), String> {
    log::info!(
        "Scraping data for product: {} with link: {}",
        source.product_id,
        &source.site_link
    );
    let scrape_result = sites::scrape(&source.site_link);

    match scrape_result {
        Ok(mut price_found) => {
            log::info!(
                "Price £{:.2} found for product: {}",
                price_found.price,
                source.product_id
            );

            let historical_low_price = get_historical_low_for_product(conn, source.product_id);

            let notification_type = add_new_price(
                conn,
                source.product_id,
                source.site_id,
                &mut price_found,
                &historical_low_price,
            )
            .unwrap();

            // Get list of users who need to be informed
            match notification_type {
                notifications::Notifications::FirstPrice
                | notifications::Notifications::PriceHasIncreased
                | notifications::Notifications::PriceHasDecreased
                | notifications::Notifications::HistoricalLow => {
                    // Inform users via discord webhook
                    log::info!("Price found is different, sending notifications to users");
                    let webhooks = get_webhooks_for_notify(conn, source.product_id).unwrap();
                    let image_file_name = get_image_for_product(conn, source.product_id);
                    webhooks.iter().for_each(|webhook_url| {
                        match discord::send_webhook(
                            webhook_url,
                            source,
                            &notification_type,
                            &price_found,
                            &historical_low_price,
                            &config.web_server_path_for_images,
                            &image_file_name,
                        ) {
                            Err(webhook_error) => {
                                log::warn!(
                                    "Webhook failed to send with error: {:?}",
                                    webhook_error
                                );
                            }
                            _ => (),
                        }
                    });
                }
                notifications::Notifications::_Error => (),
                notifications::Notifications::None => (),
            }
            Ok(())
        }
        Err(err) => Err(err),
    }
}

fn import_from_argumnet(
    conn: &mut Connection,
    args: &[String],
    config: &Config,
) -> Result<(), String> {
    let site_to_import = args.get(2);
    match site_to_import {
        Some(site_to_import) => {
            let game_found = sites::import(site_to_import);
            match game_found {
                Ok(game) => {
                    let add_game_to_db_result = add_game(conn, &game, &config.image_save_path);
                    match add_game_to_db_result {
                        Ok(()) => Ok(()),
                        Err(e) => Err(format!("Error adding game to database: {}", e)),
                    }
                }
                Err(e) => Err(e),
            }
        }
        None => Err(format!("No site given for import")),
    }
}
