# scienceHubID
Determining what are the best science hubs around the world.

## Setup

This project requires Python 3 and the `anystyle-cli` RubyGem.

### 1. Install Python

Ensure you have Python 3 installed on your system. You can download it from [python.org](https://www.python.org/).

### 2. Install Ruby and anystyle-cli

The `anystyle-cli` tool is used to parse bibliographic references. You can install it with the following commands:

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

### 3. Usage

To run the script, use the following command:

```bash
python3 main.py <input_file.csv> <output_file.csv>
```

Replace `<input_file.csv>` with the path to your input CSV file and `<output_file.csv>` with the path where you want to save the filtered results.
