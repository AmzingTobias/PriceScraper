pub mod discord;

pub enum Notifications {
    None,
    PriceHasDecreased,
    PriceHasIncreased,
    HistoricalLow,
    FirstPrice,
    _Error,
}
