<div align="center">

# SpiritByte

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/Flet-UI_Framework-0085FF)
![Storage](https://img.shields.io/badge/Storage-Local_Only-111111)
![Security](https://img.shields.io/badge/Security-Argon2id_%2B_Fernet-5C2D91)
![License](https://img.shields.io/badge/License-MIT-000000)

</div>

A local password manager built with Python and Flet, focused first on security and offline use.

## Features

- **Master password flow** with first-run setup, unlock, and auto-lock.
- **Encrypted local vault** for credentials, categories, favorites, notes, and search.
- **Recovery phrase flow** with password reset after recovery.
- **Built-in customization** for accent color, text colors, wallpapers, and overlay opacity.
- **Password tools** including generator, copy actions, and category icon selection.
- **Fully local** with no telemetry, no sync, and no network dependency.

## Requirements

- Python 3.10+
- Windows, macOS, or Linux
- Main dependencies from `requirements.txt`:
  - `flet`
  - `cryptography`
  - `argon2-cffi`
  - `mnemonic`
  - `qrcode`
  - `Pillow`

## Installation

```bash
cd SpiritByte
python -m venv venv
```

```bash
venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```

> [!NOTE]
> On first run, SpiritByte asks you to create a master password with a minimum of 12 characters.

> [!TIP]
> If you only want to use the app and do not need to clone, modify, or study the project, you can download `v1.0.0` directly from the repository Releases section.

## Build options

> [!NOTE]
> This repository currently includes two PyInstaller specs to test packaging and startup behavior.

- **`SpiritByte.spec`**
  - Build type `onedir`
  - Uses an output folder with dependencies
  - Usually opens faster
  - Usually more stable

- **`SpiritByte.onefile.spec`**
  - Build type `onefile`
  - Produces a single `.exe`
  - Usually opens slower on startup
  - Can extract temporary runtime files internally

> [!NOTE]
> - In personal testing, I did not notice a major real-world performance difference between both builds.
> - The included specs are configured for **PyInstaller**. If you want to package the app using `flet build` instead, you will need to adapt or replace them accordingly.
> - The icon was created entirely by a talented artist named Lenn; I hope you like it.

> [!WARNING]
> When running the `.exe`, Windows SmartScreen may show a security warning. This is expected — the executable is not code-signed. You can proceed by clicking **"More info" → "Run anyway"**.

> [!IMPORTANT]
> The `.exe` and the `app_data` folder must remain in the same directory. If you move either one, SpiritByte will not find the existing vault and will start fresh — creating a new `app_data` and asking you to set up a new master password.

## Data storage

On first launch, SpiritByte creates an `app_data` folder next to the executable (or `main.py`). This folder contains:

- The master password hash (Argon2id)
- The encrypted vault
- Application settings

## Project structure

```
SpiritByte/
├── src/
│   ├── main.py
│   ├── app_state.py
│   ├── core/
│   │   ├── security.py
│   │   └── recovery.py
│   ├── data/
│   │   ├── settings.py
│   │   ├── vault.py
│   │   ├── password_generator.py
│   │   └── wallpaper_store.py
│   └── ui/
│       ├── ascii_lock.py
│       ├── background_layer.py
│       ├── splash.py
│       ├── login.py
│       ├── main_view.py
│       ├── vault_dialogs.py
│       ├── recovery_dialogs.py
│       ├── color_picker.py
│       └── wallpaper_picker.py
├── assets/
├── app_data/
├── SpiritByte.spec
├── SpiritByte.onefile.spec
└── requirements.txt
```

## Security

- **Password hashing**: Argon2id
- **Key derivation**: PBKDF2-HMAC-SHA256 with 600,000 iterations
- **Vault encryption**: Fernet
- **Recovery**: 12-word phrase flow
- **Data model**: local files only

> [!IMPORTANT]
> The main priority of this project is security. UI smoothness matters, but security comes first.

> [!TIP]
> I also plan to explore a future version built with other technologies, possibly Node-based, to combine robust security with a smoother desktop experience than Flet currently offers.

<div align="center">
<h2>License</h2>

MIT

</div>
