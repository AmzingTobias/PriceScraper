use rusqlite::{Connection, Error, params};
use std::{
    fs::{File, remove_file},
    io::Write,
    path::{Path, PathBuf},
    time::SystemTime,
};
use uuid::Uuid;

use crate::{
    PriceInfo,
    notifications::Notifications,
    sites::{GameImport, Image},
};

pub fn init_db(conn: &mut Connection) -> Result<(), Error> {
    let transaction = conn.transaction().unwrap();
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Sources' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'Product_Id'	INTEGER NOT NULL,
        'Site_link'	TEXT NOT NULL,
        UNIQUE('Product_Id','Site_link'),
        FOREIGN KEY('Product_Id') REFERENCES 'Products'('Id') ON DELETE CASCADE,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Prices' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'Product_Id'	INTEGER NOT NULL,
        'Date'	INTEGER NOT NULL,
        'Price'	REAL,
        'Site_Id'	INTEGER,
        UNIQUE('Date','Product_Id'),
        FOREIGN KEY('Site_Id') REFERENCES 'Sources'('Id') ON DELETE SET NULL ON UPDATE SET NULL,
        FOREIGN KEY('Product_Id') REFERENCES 'Products'('Id') ON DELETE CASCADE ON UPDATE CASCADE,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Discord_webhooks' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'User_Id'	INTEGER NOT NULL UNIQUE,
        'Discord_webhook'	TEXT NOT NULL,
        FOREIGN KEY('User_Id') REFERENCES 'Users'('Id') ON UPDATE CASCADE ON DELETE CASCADE,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Notifications' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'User_Id'	INTEGER NOT NULL UNIQUE,
        'Enabled'	INTEGER NOT NULL,
        FOREIGN KEY('User_Id') REFERENCES 'Users'('Id') ON UPDATE CASCADE ON DELETE CASCADE,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Users' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'Username'	TEXT NOT NULL UNIQUE,
        'Password'	TEXT NOT NULL,
        'Date_created'	TEXT NOT NULL,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Product_notifications' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'Product_Id'	INTEGER NOT NULL,
        'User_Id'	INTEGER NOT NULL,
        FOREIGN KEY('Product_Id') REFERENCES 'Products'('Id') ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY('User_Id') REFERENCES 'Users'('Id') ON UPDATE CASCADE ON DELETE CASCADE,
        UNIQUE('Product_Id','User_Id'),
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Emails' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'User_Id'	INTEGER NOT NULL UNIQUE,
        'Email'	TEXT NOT NULL UNIQUE,
        FOREIGN KEY('User_Id') REFERENCES 'Users'('Id') ON UPDATE CASCADE ON DELETE CASCADE,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Admins' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'User_Id'	INTEGER NOT NULL UNIQUE,
        FOREIGN KEY('User_Id') REFERENCES 'Users'('Id') ON UPDATE CASCADE ON DELETE CASCADE,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Images' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'Image_link'	TEXT NOT NULL UNIQUE,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.execute(
        "CREATE TABLE IF NOT EXISTS 'Products' (
        'Id'	INTEGER NOT NULL UNIQUE,
        'Name'	TEXT NOT NULL UNIQUE,
        'Description'	TEXT,
        'Image_Id'	INTEGER,
        FOREIGN KEY('Image_Id') REFERENCES 'Images'('Id') ON UPDATE CASCADE ON DELETE SET NULL,
        PRIMARY KEY('Id' AUTOINCREMENT));",
        (),
    )?;
    transaction.commit()?;
    return Ok(());
}

pub fn add_new_price(
    conn: &mut Connection,
    product_id: u32,
    site_id: u32,
    price_info: &mut PriceInfo,
    historical_low_price: &Option<PriceInfo>,
) -> Result<Notifications, Box<dyn std::error::Error>> {
    let transaction = conn.transaction()?;
    let mut users_need_notification = Notifications::None;

    // First retrieve the most recent price for the product
    let previous_price: Result<f64, rusqlite::Error> = transaction.query_row(
        "SELECT Price FROM Prices Where Product_Id = ?1 ORDER BY Date DESC LIMIT 1",
        [product_id],
        |row| row.get(0),
    );

    if let Ok(previous_price) = previous_price {
        price_info.previous_price = Some(previous_price);
        if previous_price < price_info.price {
            users_need_notification = Notifications::PriceHasIncreased;
        } else if previous_price > price_info.price {
            users_need_notification = Notifications::PriceHasDecreased;
        }
    } else {
        // Product probably isn't in the database and has just found a price
        users_need_notification = Notifications::FirstPrice;
    }

    if let Some(historical_low_price) = historical_low_price {
        log::info!("Historical low found: {}", historical_low_price.price);
        if price_info.price < historical_low_price.price {
            users_need_notification = Notifications::HistoricalLow
        }
    }

    // Insert the new price into the database
    let insert_result = transaction.execute(
        "INSERT INTO Prices(Product_Id, Date, Price, Site_Id) VALUES (?1, ?2, ?3, ?4)",
        params![
            product_id,
            price_info
                .timestamp
                .duration_since(SystemTime::UNIX_EPOCH)?
                .as_secs(),
            price_info.price,
            site_id
        ],
    )?;

    transaction.commit()?;

    // If the price is different and inserted succesfully, users need to be notified
    if insert_result < 1 {
        users_need_notification = Notifications::None;
    }
    Ok(users_need_notification)
}

#[derive(Debug)]
pub struct Sources {
    pub product_id: u32,
    pub site_id: u32,
    pub site_link: String,
    pub product_name: String,
}

pub fn get_sources(conn: &Connection) -> Result<Vec<Sources>, Error> {
    let mut statement = conn.prepare(
        "SELECT Sources.Id, Site_link, Sources.Product_Id, Products.Name
    FROM Sources 
    LEFT JOIN Products ON Sources.Product_Id = Products.Id 
    ORDER BY Product_Id;",
    )?;
    let sources_iter = statement.query_map([], |row| {
        Ok(Sources {
            site_id: row.get(0)?,
            site_link: row.get(1)?,
            product_id: row.get(2)?,
            product_name: row.get(3)?,
        })
    })?;

    let mut sources = Vec::new();
    for src in sources_iter {
        sources.push(src?);
    }

    return Ok(sources);
}

fn save_imgae_locally(image: &Image, root_save_path: &PathBuf) -> Option<String> {
    // Generate a random UUID for image name
    let image_id = Uuid::new_v4();
    // Append name with extension
    let image_filename = format!("{}.{}", image_id, image.extension);
    // Create the complete path the image will be saved to
    let image_file_path = Path::new(root_save_path).join(&image_filename);
    // Create a file at the given path
    match File::create(&image_file_path) {
        // Write the image bytes to the created file
        Ok(mut file) => match file.write_all(&image.raw) {
            // If all okay, return the file name that was used for the image
            Ok(_) => Some(image_filename),
            Err(err) => {
                log::error!("Error writing image to file: {}", err);
                None
            }
        },
        Err(err) => {
            log::error!("Error creating image file: {}", err);
            None
        }
    }
}

pub fn get_image_for_product(conn: &mut Connection, product_id: u32) -> Option<String> {
    // First retrieve the most recent price for the product
    let image_link: Result<String, rusqlite::Error> = conn.query_row(
        "SELECT Image_link FROM Images LEFT JOIN Products ON Products.Image_Id = Images.Id WHERE Products.Id = ?1",
        [product_id],
        |row| row.get(0),
    );
    match image_link {
        Ok(image_link) => Some(image_link),
        Err(err) => {
            log::warn!(
                "Error fetching image for product: {}, with error: {}",
                product_id,
                err
            );
            None
        }
    }
}

pub fn add_game(
    conn: &mut Connection,
    import_data: &GameImport,
    image_save_path: &PathBuf,
) -> Result<(), Box<dyn std::error::Error>> {
    let transaction = conn.transaction()?;

    // Defined here incase an image has not been used
    let mut image_insert_id: Option<i64> = None;
    let mut image_file_name: Option<String> = None;

    // If there is an image to save
    if let Some(image) = &import_data.image {
        // Save image to the file system
        image_file_name = save_imgae_locally(image, image_save_path);
        match &image_file_name {
            // If the image was saved to the file system, insert these details to the database
            Some(file_name) => {
                transaction.execute(
                    "INSERT INTO Images (Image_link) VALUES (?1)",
                    params![file_name],
                )?;
                // Retrieve the image id for future use
                image_insert_id = Some(transaction.last_insert_rowid());
            }
            _ => (),
        }
    }

    transaction
        .execute(
            "INSERT INTO Products (Name, Description, Image_Id) VALUES (?1, ?2, ?3)",
            params![
                import_data.title,
                import_data.description.clone().unwrap_or_default(),
                image_insert_id,
            ],
        )
        .or_else(|err| {
            // If the product details could not be added to the database, delete the associated image from the file system if it exists.
            if let Some(file_name) = &image_file_name {
                let image_file_path = Path::new(image_save_path).join(&file_name);
                log::error!(
                    "Product could not be added to the database, deleting image from file system"
                );
                let remove_file_res = remove_file(image_file_path);
                if remove_file_res.is_err() {
                    log::error!("{:?}", remove_file_res.err());
                }
            }
            return Err(err);
        })?;

    let product_id = transaction.last_insert_rowid();

    transaction.execute(
        "INSERT INTO Sources (Product_Id, Site_link) VALUES (?1, ?2)",
        params![product_id, import_data.url],
    )?;

    transaction.commit()?;
    Ok(())
}

pub fn get_webhooks_for_notify(
    conn: &mut Connection,
    product_id: u32,
) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let mut statement = conn.prepare(
        "SELECT Discord_webhook FROM Discord_webhooks
INNER JOIN Product_notifications ON Discord_webhooks.User_Id = Product_notifications.User_Id
LEFT JOIN Notifications ON Notifications.User_Id = Discord_webhooks.User_Id
WHERE Product_notifications.Product_Id = ?1 AND Notifications.Enabled = 1 ;",
    )?;
    let sources_iter = statement.query_map([product_id], |row| Ok(row.get(0)?))?;

    let mut sources = Vec::new();
    for src in sources_iter {
        sources.push(src?);
    }

    return Ok(sources);
}

pub fn get_historical_low_for_product(conn: &Connection, product_id: u32) -> Option<PriceInfo> {
    let historical_low: Result<PriceInfo, rusqlite::Error> = conn.query_row(
        "SELECT p.Price, MAX(p.Date) AS Date
            FROM Prices p
            JOIN (
                SELECT Product_Id, MIN(Price) AS MinPrice
                FROM Prices
                WHERE Product_Id = ?1
                GROUP BY Product_Id
            ) lp ON p.Product_Id = lp.Product_Id AND p.Price = lp.MinPrice
            WHERE p.Product_Id = ?1
            GROUP BY p.Product_Id, p.Price",
        [product_id],
        |row| {
            Ok(PriceInfo {
                price: row.get(0)?,
                timestamp: std::time::UNIX_EPOCH + std::time::Duration::from_secs(row.get(1)?),
                previous_price: None,
            })
        },
    );
    match historical_low {
        Ok(historical_low) => Some(historical_low),
        Err(sql_error) => {
            log::warn!("{sql_error}");
            None
        }
    }
}
