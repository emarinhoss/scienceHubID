# scienceHubID
Determining what are the best science hubs around the world.

## Overview

This tool filters journal articles from patent reference data by parsing bibliographic references and identifying which ones are journal articles. It supports two parsing engines:

- **anystyle-cli** (Ruby-based, easier setup)
- **GROBID** (Python-based, higher accuracy)

## Setup

### 1. Install Python

Ensure you have Python 3 installed on your system. You can download it from [python.org](https://www.python.org/).

### 2. Choose a Parser

You can use either **anystyle-cli** or **GROBID**. Choose one based on your needs:

#### Option A: anystyle-cli (Recommended for Quick Start)

The `anystyle-cli` tool is easier to set up but requires Ruby.

**On Debian/Ubuntu:**

```bash
sudo apt-get update
sudo apt-get install -y ruby rubygems ruby-dev
sudo gem install anystyle-cli
```

**On macOS (with Homebrew):**

```bash
brew install ruby
gem install anystyle-cli
```

#### Option B: GROBID (Recommended for Higher Accuracy)

GROBID provides better accuracy but requires running a server.

**Install Python client:**

```bash
pip install grobid-client-python
```

**Run GROBID server using Docker:**

```bash
docker pull lfoppiano/grobid:0.8.0
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0
```

The GROBID server will be available at `http://localhost:8070`.

Alternatively, follow the [GROBID installation guide](https://grobid.readthedocs.io/en/latest/Install-Grobid/) for other installation methods.

## Usage

### Basic Usage (using anystyle)

```bash
python3 main.py <input_file.csv> <output_file.csv>
```

### Using GROBID

```bash
# Make sure GROBID server is running first
python3 main.py <input_file.csv> <output_file.csv> --parser grobid
```

### Advanced Options

```bash
# Explicitly specify anystyle
python3 main.py input.csv output.csv --parser anystyle

# Use GROBID with custom server URL
python3 main.py input.csv output.csv --parser grobid --grobid-server http://localhost:8080

# Show help
python3 main.py --help
```

### Input Format

The input CSV file must contain a column named `other_reference_text` with bibliographic references. Example:

```csv
other_reference_text
"Smith J, et al. Nature. 2020;123:456-789"
"US Patent 12345678"
"Jones A. Science Journal. 2019;45(2):123-130"
```

### Output Format

The output CSV has the same structure as the input, but only includes rows where the reference was classified as a journal article.

## Comparison of Parsers

| Feature | anystyle-cli | GROBID |
|---------|-------------|---------|
| **Accuracy** | Good | Very High (0.87 recall, 0.91 precision) |
| **Setup** | Medium (requires Ruby) | Medium (requires server) |
| **Speed** | Fast | Very Fast (~814 citations/s) |
| **Language** | Ruby | Java (with Python client) |
| **Recommended for** | Quick start, small datasets | Production use, large datasets |
