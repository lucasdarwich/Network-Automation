# main.py
# Genera archivos .cfg en ./configs a partir de modelo_datos.yaml y templates Jinja2
import os
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = "templates"
CONFIGS_DIR = "configs"
MODEL_FILE = "modelo.yaml"

def load_model(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # Soporta raíz en 'modelo' (nuestro diseño) o plano (por si el profe lo trae distinto)
    return data.get("modelo", data)

def j2_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        undefined=StrictUndefined,      # si falta un dato, que falle (mejor para depurar)
        trim_blocks=True,
        lstrip_blocks=True,
    )

def ensure_dirs():
    Path(CONFIGS_DIR).mkdir(parents=True, exist_ok=True)

def list_to_allowed_vlans(vlan_list):
    """Convierte [{'id':10}, ...] -> '10,20,30'"""
    return ",".join(str(v["id"]) for v in vlan_list)

def build_context(device: dict, data_path: str, global_vlans: list | None) -> dict:
    """
    Devuelve el contexto esperado por el template:
    - Pasa 'hostname'
    - Pasa el bloque nombrado por data_path (ej: 'vlans', 'trunk_interfaces', 'stp', etc.)
    - Caso especial 'port_channel': agrega 'allowed_vlans'
    """
    ctx = {"hostname": device["hostname"]}

    # Datos del propio device
    if data_path in device:
        ctx[data_path] = device[data_path]
    else:
        # permitir que falte en el device si el template no lo requiere explícitamente
        ctx[data_path] = None

    # Caso especial: port_channel.j2 espera 'allowed_vlans'
    if data_path == "port_channel":
        # Prioriza las VLANs del device; sino intenta usar globales
        vlans = device.get("vlans") or global_vlans or []
        ctx["allowed_vlans"] = list_to_allowed_vlans(vlans)

    return ctx

def main():
    ensure_dirs()
    env = j2_env()

    model = load_model(MODEL_FILE)

    # Intentamos detectar vlans globales por si hace falta (no obligatorio)
    global_vlans = None
    try:
        # si existiera modelo.globals.vlans (no siempre está)
        global_vlans = model.get("globals", {}).get("vlans")
    except Exception:
        global_vlans = None

    devices = model["infra_spec"]["devices"]

    for dev in devices:
        hostname = dev["hostname"]
        print(f"\n=== Procesando {hostname} ===")

        # Cada device trae su 'config_spec' con items: data_path, template, config_file
        specs = dev.get("config_spec", [])
        if not specs:
            print(f"[AVISO] {hostname} no tiene 'config_spec'; nada para generar.")
            continue

        for spec in specs:
            data_path   = spec["data_path"]     # p.ej. 'vlans', 'trunk_interfaces', 'access_interfaces', 'port_channel', 'stp'
            template_fn = spec["template"]      # p.ej. 'vlans.j2'
            out_fn      = spec["config_file"]   # p.ej. 'vlans.cfg'

            # Render
            template = env.get_template(template_fn)
            ctx = build_context(dev, data_path, global_vlans)
            rendered = template.render(**ctx).strip() + "\n"

            # Nombre final: Host_configfile (igual al patrón del profe)
            final_name = f"{hostname}_{out_fn}"
            out_path = Path(CONFIGS_DIR) / final_name

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered)

            print(f"  -> generado: {out_path}")

    print("\nListo. Archivos .cfg en ./configs")

if __name__ == "__main__":
    main()
