# 🧾 Laboratorio de Automatización de Switches Cisco

## 📍 Proyecto: _Automatización de Configuración de Switches con Python + Netmiko + Jinja2 + YAML_

---

## 🧠 Objetivo

Automatizar la configuración de una topología compuesta por **2 switches core** y **3 switches de acceso**, generando y aplicando de forma automática:

- VLANs (10, 20, 30)
- Interfaces **trunk** (hacia otros switches)
- Interfaces **access** (hacia hosts)
- **Port-channel LACP** entre los dos cores
- **Spanning-Tree Protocol (STP)** con balanceo de raíz por VLAN
- Archivos de configuración `.cfg` generados automáticamente a partir de plantillas Jinja2.

---

## 🧩 Tecnologías y Librerías Utilizadas

| Componente                                     | Función                                               | Librería / Herramienta |
| ---------------------------------------------- | ----------------------------------------------------- | ---------------------- |
| Python 3.11+                                   | Lenguaje base                                         | —                      |
| [Jinja2](https://palletsprojects.com/p/jinja/) | Motor de plantillas para generar configuraciones      | `pip install jinja2`   |
| [PyYAML](https://pyyaml.org/)                  | Lectura del modelo YAML de red                        | `pip install pyyaml`   |
| [Netmiko](https://github.com/ktbyers/netmiko)  | Conexión SSH y envío de comandos a equipos Cisco      | `pip install netmiko`  |
| YAML                                           | Modelo de datos del laboratorio (`modelo_datos.yaml`) | —                      |
| Markdown                                       | Documentación del proyecto (`README.md`)              | —                      |

---

## 🧱 Estructura de Carpetas

```
laboratorio1/
├─ main.py → Genera los archivos .cfg a partir del modelo y las plantillas
├─ apply.py → Aplica (vía Netmiko) las configuraciones generadas a los switches
├─ modelo.yaml → Modelo de red (inventario + templates + parámetros)
│
├─ templates/ → Plantillas Jinja2
│ ├─ vlans.j2
│ ├─ int_trunk.j2
│ ├─ int_access.j2
│ ├─ port_channel.j2
│ └─ stp.j2
│
└─ configs/ → Archivos .cfg generados por main.py
├─ SwitchCore_1_vlans.cfg
├─ SwitchCore_1_port_channel.cfg
├─ ...
└─ SwitchC_int_access.cfg
```

## ⚙️ Flujo de Automatización

```
[1] modelos.yaml
↓
[2] main.py
↓ (usa Jinja2)
[3] templates/.j2 ─────> Genera configs/.cfg
↓
[4] apply.py (usa Netmiko)
↓
[5] Switches Cisco (CLI)
```

## 📘 Descripción de Archivos

### 🧮 1. modelo.yaml

Contiene toda la información de la topología, dividida por dispositivo.  
Incluye:

- `hostname`
- `connection` (IP, credenciales, tipo de dispositivo)
- `vlans`
- `trunk_interfaces`
- `access_interfaces`
- `port_channel`
- `stp`  
  Y un bloque `config_spec` que indica **qué plantilla usar** y **cómo se llamará el archivo .cfg resultante**.

👉 Cada switch tiene sus propios datos y templates asociados.

### 🧰 2. main.py

Script principal que:

- Lee el modelo YAML
- Crea un **entorno Jinja2**
- Genera los archivos `.cfg` dentro de `/configs`
- No envía nada al equipo (solo crea archivos)

✅ Salida típica:

```
=== Procesando SwitchCore_1 ===
-> generado: configs\SwitchCore_1_vlans.cfg
-> generado: configs\SwitchCore_1_port_channel.cfg
-> generado: configs\SwitchCore_1_int_trunk.cfg
-> generado: configs\SwitchCore_1_int_access.cfg
-> generado: configs\SwitchCore_1_stp.cfg
```

### 🚀 3. apply.py

Script que:

- Lee nuevamente el modelo YAML
- Recorre los `.cfg` generados
- Se conecta por SSH (Netmiko)
- Envía los comandos (línea por línea)
- Ejecuta `write memory` para guardar la configuración

Tiene un **modo de simulación**:

```python

DRY_RUN = True
DRY_RUN = False
```

Además, filtra líneas vacías o de comentario (!) y evita errores de tiempo con cmd_verify=False y read_timeout=0

## 🧩 Templates Jinja2

### vlans.j2

```
! ========= VLANs =========
{% for v in vlans %}
vlan {{ v.id }}
name {{ v.name }}
exit
{% endfor %}
```

### int_trunk.j2

```
! ========= TRUNK INTERFACES =========
{% for iface in trunk_interfaces %}
interface {{ iface.name }}
description {{ iface.description }}
switchport trunk encapsulation dot1q
switchport mode {{ iface.mode }}
switchport trunk allowed vlan {{ iface.allowed_vlans }}
no shutdown
exit
{% endfor %}
```

### int_access.j2

```
! ========= ACCESS INTERFACES =========
{% for iface in access_interfaces %}
interface {{ iface.name }}
description {{ iface.description }}
switchport mode {{ iface.mode }}
switchport access vlan {{ iface.vlan }}
no shutdown
exit
{% endfor %}
```

### port_channel.j2

```
! ========= PORT-CHANNEL =========
{% set pcid = port_channel.id %}
{% for ifname in port_channel.members %}
interface {{ ifname }}
description {{ port_channel.description }}
channel-group {{ pcid }} mode active
no shutdown
exit
{% endfor %}
interface Port-channel{{ pcid }}
description {{ port_channel.description }}
switchport mode trunk
switchport trunk allowed vlan {{ allowed_vlans }}
no shutdown
exit
```

### stp.j2

```
! ========= STP GLOBAL =========
spanning-tree mode {{ stp.mode }}
{% for line in stp.commands %}
{{ line }}
{% endfor %}
```

## 🔐 Configuraciones Generadas (Ejemplo)

### configs/SwitchCore_1_vlans.cfg

```
vlan 10
name Ingenieria
exit
vlan 20
name Produccion
exit
vlan 30
name Finanzas
exit
```

### configs/SwitchCore_1_stp.cfg

```
spanning-tree mode rapid-pvst
spanning-tree vlan 10 root primary
spanning-tree vlan 30 root primary
spanning-tree vlan 20 root secondary
```

### configs/SwitchCore_1_port_channel.cfg

```
interface GigabitEthernet1/0
description ICL to SwitchCore_2
channel-group 1 mode active
no shutdown
exit
interface GigabitEthernet1/1
description ICL to SwitchCore_2
channel-group 1 mode active
no shutdown
exit
interface Port-channel1
description ICL to SwitchCore_2
switchport mode trunk
switchport trunk allowed vlan 10,20,30
no shutdown
exit
```

## ⚙️ Modo de Ejecución

### 🔹 Paso 1 — Generar .cfg

```bash
python main.py
```

### 🔹 Paso 2 — Ver configuración (sin aplicar)

```bash
python apply.py
```

### 🔹 Paso 3 — Aplicar configuración en los switches

```bash
# En apply.py:
DRY_RUN = False
python apply.py
```

## 🧪 Comandos de Verificación

### En los Switches Core

```bash
show vlan brief
show etherchannel summary
show interfaces trunk
show spanning-tree vlan 10 | include Root
show spanning-tree vlan 20 | include Root
show spanning-tree vlan 30 | include Root
```

### En los Switches Acceso

```bash
show interfaces trunk
show interfaces status | include Gi1
show vlan brief | include 10|20|30
```

## 🧰 Problemas Frecuentes y Soluciones

| Problema                                        | Causa                              | Solución                                                      |
| ----------------------------------------------- | ---------------------------------- | ------------------------------------------------------------- |
| `Pattern not detected`                          | Jinja genera líneas con `!`        | Filtrar comentarios o usar `cmd_verify=False`                 |
| `read_channel_timing's absolute timer expired`  | Archivo vacío o logs de STP        | Ignorar `.cfg` vacíos y usar `read_timeout=0`                 |
| `Command rejected: trunk encapsulation is auto` | Interfaz sin encapsulación fija    | Agregar `switchport trunk encapsulation dot1q` en el template |
| Port-channel en estado “D” o “I”                | Configuración distinta entre cores | Asegurar mismos puertos, modo `active`, VLANs y ID            |

## ✍️ Autor

```
Lucas Darwich
Proyecto de laboratorio de automatización de redes – Curso de Network Automation 2025

Tecnologías: Python, YAML, Jinja2, Netmiko, Cisco IOS.
Topología: 2 Cores + 3 Access – VLANs 10/20/30 – Port-Channel LACP – STP balanceado L2.
```
