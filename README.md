
# JUSTICIO MURCIA - Proyecto de Scraping del Boletín Oficial de la Región de Murcia

Este proyecto contiene un script de Python que realiza el scraping del Boletín Oficial de la Región de Murcia para extraer información específica de los anuncios publicados.

## Requisitos

- Python 3.8 o superior
- Google Chrome
- Google Chrome Driver
- WSL Ubuntu/Debian 20.04

## Instalación

### Clonar el Repositorio

```bash
git clone https://github.com/juanbaCubic/justicioMurcia.git ./justicioMurcia
cd justicioMurcia
```

### Crear y Activar un Entorno Virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Cambiar permisos del ejecutable

```bash
sudo chmod +x justicioMurcia.py
```

### Instalar Google Chrome

Este proyecto se ha desarrollado en WSL (Windows Subsystem for Linux) Ubuntu/Debian 20.04. Puedes instalar Google Chrome usando los siguientes comandos:

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

### Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto y añade las siguientes variables:

```
BASE_PATH=.
DOCUMENT_PATH=./borm/dias
SLEEP_TIME=2
```

## Uso

### Extraer Información Para Una Fecha

Para ejecutar el script de scraping y obtener los resultados para una fecha concreta:

```bash
./justicioMurcia.py 2024-06-15
```

### Extraer Información Entre Fechas

Para extraer información de un rango de fechas:

```bash
./justicioMurcia.py 2024-06-01 2024-06-15
```

## Estructura del Proyecto

- `justicioMurcia.py`: Script principal para realizar el scraping.
- `requirements.txt`: Lista de dependencias necesarias.
- `.env`: Archivo con variables de entorno utilizadas en el código.
- `.gitignore`: Archivo para ignorar archivos y directorios en el control de versiones.

## Notas

- Asegúrate de tener Google Chrome y ChromeDriver correctamente instalados y configurados en tu entorno.
- Este script está diseñado para ser robusto y manejar posibles cambios en la estructura HTML del boletín.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para discutir cualquier cambio que desees realizar.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.
