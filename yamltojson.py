# Convertimos el modelo YAML a JSON
import yaml
import json

MODEL_FILE = "modelo.yaml"
OUTPUT_FILE = "modelo.json"

def main():
    with open(MODEL_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Archivo JSON generado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()