import os
import time
import json
import logging
import requests
from requests.exceptions import HTTPError, RequestException
from requests_cache import CachedSession
from googletrans import Translator
from dotenv import load_dotenv

# ----------------------------
# Configuração inicial
# ----------------------------

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ Defina a variável de ambiente OPENWEATHER_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ----------------------------
# Funções utilitárias
# ----------------------------

def kelvin_to_celsius(kelvin: float) -> float:
    return round(kelvin - 273.15, 1)


def degrees_to_compass(deg: int) -> str:
    directions = [
        "N","NNE","NE","ENE","E","ESE","SE","SSE",
        "S","SSW","SW","WSW","W","WNW","NW","NNW"
    ]
    idx = int((deg + 11.25) / 22.5) % 16
    return directions[idx]


def validate_response(data: dict):
    code = data.get("cod")
    if code == "404":
        raise ValueError("❌ Cidade não encontrada")
    if code != 200:
        message = data.get("message", "Erro desconhecido")
        raise RuntimeError(f"❌ Erro da API OpenWeather: {message}")


def format_output(parsed: dict, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(parsed, ensure_ascii=False, indent=4)
    return (
        f"[{parsed['cidade']}]  \n"
        f"{parsed['temperatura']}°C (Sensação: {parsed['sensacao']}°C)  \n"
        f"Umidade: {parsed['umidade']}%  |  Vento: {parsed['vento']} m/s {parsed['wind_cardinal']}  \n"
        f"{parsed['condicao']}"
    )


# ----------------------------
# Classe auxiliar: RateLimiter
# ----------------------------

class RateLimiter:
    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._last_time = 0.0

    def wait(self):
        elapsed = time.time() - self._last_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_time = time.time()


# ----------------------------
# Classe principal: WeatherAgent
# ----------------------------

class WeatherAgent:

    def __init__(self, api_key: str, rate_limit: float = 1.0, cache_expire: int = 600):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.session = CachedSession(cache_name="weather_cache", expire_after=cache_expire)
        self.translator = Translator()
        self.rate_limiter = RateLimiter(rate_limit)

    def get_weather(self, location: str) -> dict:
        self.rate_limiter.wait()

        params = {
            "q": f"{location},BR",
            "appid": self.api_key,
            "lang": "pt"
        }

        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
        except HTTPError as http_err:
            raise RuntimeError(f"❌ HTTP error: {http_err}")
        except RequestException as req_err:
            raise RuntimeError(f"❌ Erro na requisição: {req_err}")

        return response.json()

    def map_condition(self, code: int) -> str:
            
            if 200 <= code < 300:
                return "⛈️ Tempestade"
            if 300 <= code < 400:
                return "🌦️ Garoa"
            if 500 <= code < 600:
                return "🌧️ Chuva"
            if 600 <= code < 700:
                return "❄️ Neve"
            if 700 <= code < 800:
                return "🌫️ Névoa"
            if code == 800:
                return "☀️ Céu limpo"
            if code == 801:
                return "⛅ Poucas nuvens"
            if code == 802:
                return "🌥️ Nuvens dispersas"
            if code == 803:
                return "☁️ Nuvens quebradas"
            if code == 804:
                return "☁️ Nublado"
            return "🌈 Condição indefinida"

    def analyze_weather(self, data: dict, as_json: bool = False) -> str:
        validate_response(data)

        main = data["main"]
        wind = data["wind"]
        weather = data["weather"][0]
        parsed = {
            "cidade": data.get("name"),
            "temperatura": kelvin_to_celsius(main.get("temp", 0)),
            "sensacao": kelvin_to_celsius(main.get("feels_like", 0)),
            "umidade": main.get("humidity", 0),
            "vento": wind.get("speed", 0),
            "wind_cardinal": degrees_to_compass(wind.get("deg", 0)),
            "descricao": weather.get("description", "").capitalize(),
            "condicao": self.map_condition(weather.get("id", 0)),
        }

        return format_output(parsed, as_json)

    def translate_description(self, text: str, dest: str = "pt") -> str:
        return self.translator.translate(text, dest=dest).text


# ----------------------------
# Exemplo de uso standalone
# ----------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agente Meteorológico CLI")
    parser.add_argument("cidades", nargs="+", help="Cidades (ex: São Paulo)")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    args = parser.parse_args()

    agent = WeatherAgent(API_KEY)
    for loc in args.cidades:
        try:
            raw = agent.get_weather(loc)
            output = agent.analyze_weather(raw, args.json)
            print(output, "\n")
        except Exception as e:
            logging.error(e)