import os                                     
import sys                                     
import argparse                               
import logging                               

from weather_agent import WeatherAgent         

def run_batch(agent: WeatherAgent, cidades: list[str], as_json: bool):
    print("[DEBUG] Entrou em run_batch")     
    for cidade in cidades:
        try:
            raw = agent.get_weather(cidade)
            output = agent.analyze_weather(raw, as_json)
            print(output, "\n")
        except Exception as e:
            logging.error(e)

def run_interactive(agent: WeatherAgent, as_json: bool):
    print("[DEBUG] Entrou em run_interactive")  
    print("🚀 Modo interativo: digite o nome da cidade ou 'sair' para encerrar.")
    while True:
        cidade = input("Cidade: ").strip()
        if not cidade or cidade.lower() in ("sair", "exit", "quit"):
            print("Encerrando. Até a próxima!")
            break
        try:
            raw = agent.get_weather(cidade)
            output = agent.analyze_weather(raw, as_json)
            print(output, "\n")
        except Exception as e:
            logging.error(e)

def main():
    print("[DEBUG] Iniciando main")             
    parser = argparse.ArgumentParser(
        description="Agente Meteorológico CLI (batch e interativo)"
    )
    parser.add_argument(
        "cidades",
        nargs="*",                             
        help="Cidades brasileiras (ex: São Paulo Recife). Se omitido, entra no modo interativo."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    args = parser.parse_args()
    print(f"[DEBUG] args.cidades = {args.cidades!r}")  

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        sys.exit("❌ Variável OPENWEATHER_API_KEY não definida")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    agent = WeatherAgent(api_key)

    if args.cidades:
        run_batch(agent, args.cidades, args.json)
    else:
        run_interactive(agent, args.json)

if __name__ == "__main__":
    main() 