# Schmagent

A GTK-based chat application for interacting with various AI models.

## Requirements

- Python 3.13.2 or higher
- GTK 4.0 and Libadwaita 1.0
- Various Python packages (see `requirements.txt`)

## Development Setup

### 1. Install System Dependencies

#### Fedora

```bash
sudo dnf install python3.13 python3.13-devel
sudo dnf install gtk4-devel libadwaita-devel gobject-introspection-devel
```

#### Ubuntu/Debian

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev
sudo apt install libgtk-4-dev libadwaita-1-dev libgirepository1.0-dev
```

### 2. Set Up Development Environment

We provide a setup script that creates a virtual environment and installs all dependencies:

```bash
./setup_venv.sh
```

For development dependencies (linters, formatters, etc.), use:

```bash
./setup_venv.sh --dev
```

### 3. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### 4. Run the Application

```bash
python -m schmagent
```

## Configuration

Copy the `.env.example` file to `.env` and customize the settings:

```bash
cp .env.example .env
```

Edit the `.env` file to configure API keys, model settings, and UI preferences.

## IDE Setup

This project includes configuration files for VS Code/Cursor:

- `.vscode/settings.json`: Editor settings
- `pyrightconfig.json`: Type checking configuration
- `.pylintrc`: Linting configuration
- `mypy.ini`: Type checking configuration

These files are configured to handle the GTK imports correctly, which are typically installed at the system level.

## Troubleshooting

### Import Errors in IDE

If you see import errors for GTK modules in your IDE:

1. Make sure you've run the setup script, which creates a symbolic link to the system GTK libraries
2. Restart your IDE after setup
3. Check that the Python interpreter in your IDE is set to the virtual environment

### Runtime Errors

If you encounter runtime errors related to GTK:

1. Make sure you have GTK 4.0 and Libadwaita 1.0 installed on your system
2. Check that the symbolic link to the system GTK libraries is correct
3. Try running the application from the terminal to see detailed error messages

## License

MIT
