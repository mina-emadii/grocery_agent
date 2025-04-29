# Grocery Shopping Agent

An AI-powered agent that helps users find the best grocery deals and plan their shopping trips.

## Features

- Web scraping of grocery store websites to find current prices and deals
- Price comparison across different stores
- Shopping list management
- Deal recommendations based on user preferences
- Route optimization for multi-store shopping trips

## Setup

1. Make sure you have Python 3.12.3 installed (use pyenv if needed)
2. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Run the bootstrap script:
   ```bash
   ./bootstrap.sh
   ```
4. Set your OpenAI API key in your environment:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```
5. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Project Structure

- `src/agent.py` - Main agent implementation
- `src/stores/` - Store-specific scrapers and interfaces
- `src/models/` - Data models and schemas
- `src/utils/` - Utility functions and helpers
- `tests/` - Test suite

## Usage

[Usage instructions will be added as features are implemented]

## Contributing

[Contributing guidelines will be added]

## License

MIT License 