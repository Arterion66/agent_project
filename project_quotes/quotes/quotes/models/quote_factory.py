from quotes.quotes.models.quote_entity import QuoteEntity

async def serialize_quote(quote):
    """
    Serialize a quote object to a dictionary.
    """
    quote = quote.mdoel_dump()
    return QuoteEntity(**quote)