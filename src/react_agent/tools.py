"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

import aiohttp

from typing import Any, Callable, List, Optional, cast

from langchain_tavily import TavilySearch  # type: ignore[import-not-found]

from react_agent.configuration import Configuration

from react_agent.pokemon_shcema import PokemonSchemaAPI, PokemonSchema

from react_agent.state import State
from langchain_core.messages import AIMessage
from typing import Dict, List

from datetime import datetime

async def search(query: str) -> Optional[dict[str, Any]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    configuration = Configuration.from_context()
    wrapped = TavilySearch(max_results=configuration.max_search_results)
    return cast(dict[str, Any], await wrapped.ainvoke({"query": query}))

async def search_pokemon_by_name(name: str) -> Optional[dict[str, Any]]:
    """Search for a Pokemon by name"""

    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                api_data = PokemonSchemaAPI(**data)
                pokemon = PokemonSchema.from_api(api_data)
                return pokemon
            else:
                return {"error": f"Pokemon '{name}' not found."}

async def get_pokemon_wiki(name: str) -> Optional[dict[str, Any]]:
    """Get a Pokemon's wiki page."""
    normalized = name.split("-")[0] if "-" in name else name
    normalized = normalized.lower()
    url = f"https://pokemondb.net/pokedex/{normalized}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return url
            else:
                return {"error": f"Pokemon '{name}' not found."}

async def schedule_quote(name: str, gmail: str, date: datetime) -> Optional[dict]:
    """Schedule a quote for a specific date."""
    print(date.isoformat())
    url = "http://localhost:8001/quotes/schedule"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"name": name, "gmail": gmail, "date": date.isoformat()},
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 500:
                return {"error": "Internal server error. Please try again later."}
            else:
                return await response.json()  # Devuelve el error tal cual si no es 500

async def check_availability(date: datetime) -> Optional[dict]:
    """Check availability for a given date."""
    url = f"http://localhost:8001/quotes/schedule?date={date.isoformat()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 500:
                return {"error": "Internal server error. Please try again later."}
            else:
                return await response.json()  # Devuelve el error tal cual si no es 500

async def reschedule_quote(gmail: str, new_date: datetime) -> Optional[dict]:
    """Reschedule a quote to a new date."""
    url = "http://localhost:8001/quotes/reschedule"
    async with aiohttp.ClientSession() as session:
        async with session.put(
            url, json={"gmail": gmail, "new_date": new_date.isoformat()}
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 500:
                return {"error": "Internal server error. Please try again later."}
            else:
                return await response.json()  # Devuelve el error tal cual si no es 500

async def cancel_quote(gmail: str) -> Optional[dict]:
    """Cancel a scheduled quote."""
    url = "http://localhost:8001/quotes/cancel"
    async with aiohttp.ClientSession() as session:
        async with session.put(
            url, json={"gmail": gmail}
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 500:
                return {"error": "Internal server error. Please try again later."}
            else:
                return await response.json()  # Devuelve el error tal cual si no es 500

async def send_email(gmail: str) -> Optional[dict]:
    """Send an email to the specified Gmail address."""
    url = "http://localhost:8001/emails/send"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params={"gmail": gmail}) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 500:
                return {"error": "Internal server error. Please try again later."}
            else:
                return await response.json()  # Devuelve el error tal cual si no es 500

TOOLS: List[Callable[..., Any]] = [search]

POKEMONTOOLS: List[Callable[..., Any]] = [search_pokemon_by_name, get_pokemon_wiki]

QUOTETOOLS: List[Callable[..., Any]] = [
    schedule_quote,
    check_availability,
    reschedule_quote,
    cancel_quote,
]

EMAILTOOL: List[Callable[..., Any]] = [send_email]