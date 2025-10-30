# apply.py
# Aplica los .cfg de ./configs a cada dispositivo según modelo_datos.yaml
DRY_RUN = False  # poné False para empujar al switch

import sys
from pathlib import Path
import yaml
from netmiko import ConnectHandler

MODEL_FILE = "modelo.yaml"
CONFIGS_DIR = Path("configs")

def load_model(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("modelo", data)

def read_cfg(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()

def push(host, user, pwd, cfg_text):
    if DRY_RUN:
        print(f"\n--- [DRY-RUN] {host} ---\n{cfg_text[:2000]}\n--- end ---")
        return
    from netmiko import ConnectHandler
    conn = ConnectHandler(device_type="cisco_ios", host=host, username=user, password=pwd, fast_cli=True)
    try:
        # filtra comentarios y líneas vacías
        lines = [ln for ln in cfg_text.splitlines() if ln.strip() and not ln.strip().startswith("!")]
        if not lines:
            print(f"[SKIP] {host}: no hay líneas aplicables en este .cfg")
            return

        out = conn.send_config_set(
            lines,
            cmd_verify=False,   # evita errores por líneas no “echo”
            read_timeout=0,     # lee hasta que el equipo deje de emitir
        )
        conn.save_config()
        print(f"\n=== [{host}] OK ===")
        print(out[-800:])
    finally:
        conn.disconnect()

def main():
    model = load_model(MODEL_FILE)
    devices = model["infra_spec"]["devices"]

    for dev in devices:
        hn   = dev["hostname"]
        host = dev["connection"]["host"]
        user = dev["connection"].get("username") or model["globals"]["connection"]["username"]
        pwd  = dev["connection"].get("password") or model["globals"]["connection"]["password"]
        specs = dev.get("config_spec", [])

        print(f"\n##### Aplicando en {hn} ({host}) #####")
        for spec in specs:
            out_fn = spec["config_file"]                 # ej: vlans.cfg
            cfg_path = CONFIGS_DIR / f"{hn}_{out_fn}"    # ej: configs/SwitchA_vlans.cfg
            if not cfg_path.exists():
                print(f"[SKIP] No existe {cfg_path}")
                continue
            try:
                cfg_text = read_cfg(cfg_path)
                if not cfg_text.strip():
                    print(f"[SKIP] Vacío: {cfg_path}")
                    continue
                push(host, user, pwd, cfg_text)
            except Exception as e:
                print(f"[ERROR] {hn} -> {cfg_path.name}: {e}")

    print(f"\nListo. (DRY_RUN = {DRY_RUN})")

if __name__ == "__main__":
    main()
