import os
import re
import requests
from dotenv import load_dotenv

# Load environment variables from the project's .env file
load_dotenv()

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
TAVILY_URL = "https://api.tavily.com/search"


class ServiceError(Exception):
    """Raised when a weather or news service fails."""


def normalize_city(city):
    """
    Extract a clean city name from common natural-language queries.

    Examples:
        'weather of Prayagraj' -> 'Prayagraj'
        'Current weather in Kanpur' -> 'Kanpur'
        'Show me weather in Delhi' -> 'Delhi'
    """
    if not isinstance(city, str) or not city.strip():
        raise ServiceError("Please enter a valid city name.")

    city = city.strip()

    # Remove common introductory phrases
    patterns = [
        r"^(?:please\s+)?show\s+me\s+",
        r"^(?:please\s+)?tell\s+me\s+",
        r"^(?:please\s+)?what\s+is\s+",
        r"^(?:please\s+)?get\s+",
        r"^(?:please\s+)?find\s+",
    ]

    for pattern in patterns:
        city = re.sub(pattern, "", city, flags=re.IGNORECASE)

    # Remove weather-related prefixes
    patterns = [
        r"^(?:the\s+)?current\s+weather\s+(?:of|in|for|at)\s+",
        r"^(?:the\s+)?weather\s+(?:of|in|for|at)\s+",
        r"^weather\s+",
    ]

    for pattern in patterns:
        city = re.sub(pattern, "", city, flags=re.IGNORECASE)

    # Remove common trailing words and punctuation
    city = re.sub(
        r"\s+(?:weather|today|right now|currently)\s*$",
        "",
        city,
        flags=re.IGNORECASE,
    )

    city = city.strip(" \t\r\n?!.,")
    city = re.sub(r"\s+", " ", city)

    if not city:
        raise ServiceError(
            "Could not identify the city. Try 'weather in Prayagraj'."
        )

    return city


def fetch_weather(city):
    """Fetch current weather, retrying known city-name aliases."""
    city = normalize_city(city)

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ServiceError(
            "OPENWEATHER_API_KEY is missing. Check your .env file."
        )

    # Try the requested name first, then known alternative names.
    city_names = [city]

    aliases = {
        "prayagraj": "Allahabad",
    }

    alias = aliases.get(city.casefold())
    if alias and alias.casefold() != city.casefold():
        city_names.append(alias)

    last_error = None

    for city_name in city_names:
        try:
            response = requests.get(
                OPENWEATHER_URL,
                params={
                    "q": f"{city_name},IN",
                    "appid": api_key,
                    "units": "metric",
                },
                timeout=15,
            )

            try:
                data = response.json()
            except ValueError as exc:
                raise ServiceError(
                    f"Weather API returned invalid JSON "
                    f"(HTTP {response.status_code})."
                ) from exc

            if response.status_code == 404:
                last_error = (
                    f"City '{city_name}' was not found."
                )
                continue

            if response.status_code == 401:
                raise ServiceError(
                    "OpenWeatherMap rejected the API key. "
                    "Check OPENWEATHER_API_KEY in your .env file."
                )

            if response.status_code == 429:
                raise ServiceError(
                    "Weather API rate limit reached. Try again later."
                )

            if not response.ok:
                message = data.get("message", "Request failed")
                raise ServiceError(
                    f"Weather API error (HTTP {response.status_code}): "
                    f"{message}"
                )

            weather_info = data["weather"][0]
            main_info = data["main"]

            return {
                # Preserve the requested modern city name in the UI.
                "city": city.title(),
                "temp": round(float(main_info["temp"]), 1),
                "feels_like": round(float(main_info["feels_like"]), 1),
                "description": weather_info.get(
                    "description", "Unknown"
                ).title(),
                "humidity": main_info.get("humidity", 0),
                "wind": data.get("wind", {}).get("speed", 0),
                "icon": weather_info.get("icon", ""),
            }

        except requests.Timeout as exc:
            raise ServiceError(
                "Weather API timed out. Please try again."
            ) from exc

        except requests.RequestException as exc:
            raise ServiceError(
                "Could not connect to the weather API. "
                "Check your internet connection."
            ) from exc

        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ServiceError(
                "Weather API returned an unexpected response."
            ) from exc

    raise ServiceError(
        f"Could not find weather for '{city}'. "
        f"{last_error or 'Try another city name.'} "
        "Check the city name or your OpenWeatherMap service."
    )

def fetch_news(city, n=3):
    """Fetch recent city-related news using Tavily."""
    city = normalize_city(city)

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ServiceError(
            "TAVILY_API_KEY is missing. "
            "Please check your .env file."
        )

    try:
        response = requests.post(
            TAVILY_URL,
            json={
                "api_key": api_key,
                "query": f"latest local news in {city}, India",
                "topic": "news",
                "search_depth": "basic",
                "max_results": max(1, min(int(n), 10)),
            },
            timeout=20,
        )

        try:
            data = response.json()
        except ValueError as exc:
            raise ServiceError(
                f"News API returned invalid JSON "
                f"(HTTP {response.status_code})."
            ) from exc

        if not response.ok:
            message = (
                data.get("detail")
                or data.get("message")
                or data.get("error")
                or "Request failed"
            )

            if response.status_code == 401:
                message = (
                    "Invalid or inactive Tavily API key. "
                    "Check TAVILY_API_KEY in your .env file."
                )
            elif response.status_code == 429:
                message = (
                    "Tavily API rate limit reached. "
                    "Please try again later."
                )

            raise ServiceError(
                f"News API error (HTTP {response.status_code}): "
                f"{message}"
            )

        articles = []

        for item in data.get("results", []):
            articles.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "published_date": item.get("published_date", ""),
            })

        return articles

    except requests.Timeout as exc:
        raise ServiceError(
            "News API timed out. Please try again."
        ) from exc

    except requests.RequestException as exc:
        raise ServiceError(
            "Could not connect to the news API. "
            "Check your internet connection."
        ) from exc

    except (TypeError, ValueError) as exc:
        raise ServiceError(
            "Could not process the news request. "
            "Please check the requested article count."
        ) from exc
