import logging

from discord_webhook import DiscordWebhook, DiscordEmbed

from common.product_info import PriceInfo, date_to_string, get_price_difference_string

# Title of the embedded webhook will be the game name
# Description of the embedded webhook will be talking about the price
# Footer will contain details on when the lowest price was ever recorded


# The different colours a webhook embed can be depending on the price difference
PRICE_DECREASE_COLOUR = "77dd77"
PRICE_NO_CHANGE_COLOUR = "dddd77"
PRICE_INCREASE_COLOUR = "dd7777"


class Discord:
    """
    Send discord notifications using webhook url(s) to alert for price changes

    Attributes:
        webhook_urls (list[str]): A list of webhook urls that will have the notifications sent to
        webhooks (tuple[DiscordWebhook]): A tuple of DiscordWebhook objects that are used to send the notification
    """
    webhook_urls: list[str]
    webhooks: tuple[DiscordWebhook]

    def __init__(self, webhook_urls: list[str]) -> None:
        """
        Create a webhook manager that can create and send discord webhooks. To alert if the price has changed
        :param webhook_urls: A list of discord webhook urls that will receive the notification
        """
        self.webhook_urls = webhook_urls
        self.webhooks = DiscordWebhook.create_batch(urls=webhook_urls, rate_limit_retry=True)

    def prepare_webhook(self,
                        product_name: str,
                        current_price_info: PriceInfo,
                        previous_price: PriceInfo,
                        historical_low_price: PriceInfo = PriceInfo(None, None, None),
                        product_image_link: None | str=None) -> None:
        """
        Creates the embed for the webhook
        :param product_name: The product name the embed is for
        :param current_price_info: The current price that was found for the product
        :param previous_price: The last price that was found for the product
        :param historical_low_price: The lowest all-time price that was found for the product
        """
        embed = DiscordEmbed()

        # Check a source link exists for the current price before setting the URL
        if current_price_info.source_link is not None:
            embed.set_url(current_price_info.source_link)

        embed.set_title(product_name)

        # Set the webhook colour depending on the price difference between the current and previous price
        embed = self._set_webhook_colour(embed, current_price_info.price, previous_price.price)
        # Set the footer note of the embed to show the historical low price
        embed = self._set_historical_low(embed, current_price_info.price, historical_low_price)

        if product_image_link is not None:
            if product_image_link.startswith("http://") or product_image_link.startswith("https://"):
                embed.set_image(product_image_link)

        description_sent = False
        # Check a price exists for both the price and previous price
        if current_price_info.price is not None and previous_price.price is not None:
            # Check if a historical price exists and can be used to compare
            if historical_low_price.price is not None:
                if current_price_info.price < historical_low_price.price:
                    description_sent = True
                    embed = self._set_historical_low_description(embed, current_price_info.price, previous_price.price)
            if not description_sent:
                if current_price_info.price < previous_price.price:
                    embed = self._set_price_decrease_description(embed, current_price_info.price, previous_price.price)
                elif current_price_info.price == previous_price.price:
                    embed = self._set_no_price_change_description(embed, current_price_info.price)
                else:
                    embed = self._set_price_increase_description(embed, current_price_info.price, previous_price.price)
        elif current_price_info.price is not None:
            embed = self._set_new_product_description(embed, current_price_info.price)
        # Add the embed to all webhooks
        for webhook in self.webhooks:
            webhook.add_embed(embed)

    @staticmethod
    def _set_historical_low_description(embed: DiscordEmbed, current_price: float, previous_price: float,
                                        extra_text="") -> DiscordEmbed:
        """
        Private static method to create the description of an embed, if the price is now a historical low
        :param embed: The embedded object to set the description for
        :param current_price: The current price that has been found
        :param previous_price: The previous price that was last found
        :param extra_text: Any extra text to add to the description
        :return: The embedded object that was supplied, with the description added
        """
        embed_description = f"**NEW HISTORICAL LOW**\n"
        embed_description = Discord._set_price_description(embed_description, current_price, previous_price,
                                                           extra_text)
        embed.set_description(embed_description)
        return embed

    @staticmethod
    def _set_price_decrease_description(embed: DiscordEmbed, current_price: float, previous_price: float,
                                        extra_text="") -> DiscordEmbed:
        """
        Private static method to create the description of an embed, if the price has decreased from the previous price
        :param embed: The embedded object to set the description for
        :param current_price: The current price that has been found
        :param previous_price: The previous price that was last found
        :param extra_text: Any extra text to add to the description
        :return: The embedded object that was supplied, with the description added
        """
        embed_description = f"**PRICE DECREASE**\n"
        embed_description = Discord._set_price_description(embed_description, current_price, previous_price, extra_text)
        embed.set_description(embed_description)
        return embed

    @staticmethod
    def _set_new_product_description(embed: DiscordEmbed, current_price: float, extra_text="") -> DiscordEmbed:
        embed_description = f"**PRICE FOUND**\n"
        embed_description += f"**£{current_price:.2f}**"
        if extra_text != "":
            embed_description += f"\n{extra_text}"
        embed.set_description(embed_description)
        return embed

    @staticmethod
    def _set_price_increase_description(embed: DiscordEmbed, current_price: float,
                                        previous_price: float,
                                        extra_text="") -> DiscordEmbed:
        """
        Private static method to create the description of an embed, if the price has decreased from the previous price
        :param embed: The embedded object to set the description for
        :param current_price: The current price that has been found
        :param previous_price: The previous price that was last found
        :param extra_text: Any extra text to add to the description
        :return: The embedded object that was supplied, with the description added
        """
        embed_description = f"**PRICE INCREASE**\n"
        embed_description = Discord._set_price_description(embed_description, current_price, previous_price, extra_text)
        embed.set_description(embed_description)
        return embed

    @staticmethod
    def _set_no_price_change_description(embed: DiscordEmbed, current_price: float) -> DiscordEmbed:
        """
        Private static method to create the description of an embed, if the price has not changed
        :param embed: The embedded object to set the description for
        :param current_price: The current price that has been found
        :return: The embedded object that was supplied, with the description added
        """
        embed_description = f"**NO PRICE CHANGE: £{current_price:.2f}**\n"
        embed.set_description(embed_description)
        return embed

    @staticmethod
    def _set_price_description(text: str, current_price: float, previous_price: float, extra_text="") -> str:
        """
        Generate the description text that is needed to show the difference between the current and previous prices
        :param text: Text for the description that has already been used
        :param current_price: The current price that has been found
        :param previous_price: The previous price that was last found
        :param extra_text: Any extra text to add on to the end
        :return: The text string, with the price difference added
        """
        text += f"**£{current_price:.2f}** " \
                f"{'down' if current_price < previous_price else 'up'} from £{previous_price:.2f} | " \
                f"**{get_price_difference_string(current_price, previous_price)}**"
        if extra_text != "":
            text += f"\n{extra_text}"
        return text

    @staticmethod
    def _set_webhook_colour(embed: DiscordEmbed,
                            current_price: float | None,
                            previous_price: float | None) -> DiscordEmbed:
        """
        Set the webhook colour, depending on the difference between the current and previous prices
        :param embed: The embedded object to set the description for
        :param current_price: The current price that has been found
        :param previous_price: The previous price that was last found
        :return: The embedded object that was supplied, with the colour added
        """
        if current_price is not None and previous_price is not None:
            if current_price == previous_price:
                embed.set_color(PRICE_NO_CHANGE_COLOUR)
            elif current_price < previous_price:
                embed.set_color(PRICE_DECREASE_COLOUR)
            else:
                embed.set_color(PRICE_INCREASE_COLOUR)
        else:
            embed.set_color(PRICE_DECREASE_COLOUR)
        return embed

    @staticmethod
    def _set_historical_low(embed: DiscordEmbed, current_price: float | None,
                            historical_low: PriceInfo) -> DiscordEmbed:
        """
        Set the historical low footer note if the historical low price and date exists
        :param embed: The embedded object to set the description for
        :param current_price: The current price that has been found
        :param historical_low: The lowest all-time price that was found for the product
        :return: The embedded object that was supplied, with the footer added
        """
        if historical_low is not None and historical_low.price is not None and historical_low.date is not None:
            historical_low_text = f"Historical low: £{historical_low.price:.2f}, which occurred on: " \
                                  f"{date_to_string(historical_low.date)}\n"
            historical_low_text += f"Difference of: "
            historical_low_text += get_price_difference_string(current_price, historical_low.price)
            embed.set_footer(text=historical_low_text)
        return embed

    def send_webhook(self) -> None:
        """
        Send the webhook to all webhook urls that are stored
        """
        for webhook_url, webhook in zip(self.webhook_urls, self.webhooks):
            logging.info(f"Discord Webhook sent to {webhook_url}")
            # TODO error handling on this call failing
            webhook.execute()


if __name__ == '__main__':
    print(f"{Discord.__name__}:\n{Discord.__doc__}")
    for name, method in Discord.__dict__.items():
        if callable(method) and hasattr(method, '__doc__'):
            docstring = method.__doc__
            if docstring:
                print(f"Method '{name}':\n{docstring.strip()}\n")
