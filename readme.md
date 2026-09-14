# The Blackhat
![](img/blackpants.jpg)

The Blackhat is a combination of the [Flipper Blackhat](https://github.com/o7-machinehum/flipper-blackhat) and the "Blackpants" (this repo). They combine to make a completely open source, handheld Linux computer.

## Development Setup

### Using Docker (Recommended - Self-Contained)

Build and run the Docker container with all dependencies included:

```bash
# Build the Docker image
docker-compose build

# Run the container
docker-compose run --rm hardware-build bash

# Inside the container, run any make commands
make prepare
make drc
make gerbers
make schematic
make pdfs
```

Or use Docker directly:

```bash
docker build -t blackpants:latest .
docker run -it -v ${PWD}:/workspace blackpants:latest bash
```

### Local Development (Manual Setup)

If you prefer to install tools locally:

1. **Install Make**: 
   - Windows: `choco install make` or download from GnuWin32
   - macOS: `brew install make`
   - Linux: `apt-get install make`

2. **Install Python 3.8+**

3. **Install KiCAD and CLI tools**:
   - Download from https://kicad.org

4. **Prepare environment**:
   ```bash
   make prepare
   ```

5. **Run make targets**:
   ```bash
   make drc
   make gerbers
   make schematic
   make pdfs
   ```

## Make Targets

### Blackpants Board
- `make drc` - Run design rule checks
- `make gerbers` - Generate Gerber files for manufacturing
- `make schematic` - Export schematic to PDF
- `make pdfs` - Export PCB layers to PDF

### Backward Compatibility Aliases
- `make drc_carrier` - Alias for `make drc`
- `make gerbers_carrier` - Alias for `make gerbers`
- `make schematic_carrier` - Alias for `make schematic`
- `make pdfs_carrier` - Alias for `make pdfs`
- `make drc_m2` - Alias for `make drc`
- `make gerbers_m2` - Alias for `make gerbers`
- `make schematic_m2` - Alias for `make schematic`
- `make pdfs_m2` - Alias for `make pdfs`

### Utilities
- `make clean` - Remove all generated production files and PDFs
- `make prepare` - Install kikit (only needed for local development)
- `make remove_env` - Remove Python virtual environment (deprecated, not used in Docker)

