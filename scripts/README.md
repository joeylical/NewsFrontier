# Database Initialization Scripts

This directory contains the modular database initialization system for NewsFrontier.

## Overview

The system uses a template-based approach with separate configuration files to make it easy to modify settings and prompts without touching the script code.

## File Structure

```
scripts/
├── init.sql.template      # SQL template with placeholders
├── init.sql              # Generated SQL file (do not edit directly)
├── generate-init-sql.py   # Python script to generate init.sql from template
├── config.json           # Main configuration file
└── prompts/              # Directory containing prompt files
    ├── topics_extraction.txt
    ├── entities_extraction.txt
    ├── keywords_extraction.txt
    ├── sentiment_analysis.txt
    └── summary_creation.txt
```

## Usage

### Generate Database Schema

```bash
cd scripts
python3 generate-init-sql.py
```

This will:
1. Read configuration from `config.json`
2. Load prompt files from `prompts/` directory
3. Replace placeholders in `init.sql.template`
4. Generate the final `init.sql` file

### Configuration

Edit `config.json` to modify database settings:

```json
{
  "database": {
    "embedding_dimension": 1536,
    "default_rss_fetch_interval": 60,
    "max_processing_attempts": 3,
    "similarity_threshold": 0.7,
    "max_articles_per_event": 50
  },
  "prompts": {
    "topics_extraction": "prompts/topics_extraction.txt",
    "entities_extraction": "prompts/entities_extraction.txt", 
    "keywords_extraction": "prompts/keywords_extraction.txt",
    "sentiment_analysis": "prompts/sentiment_analysis.txt",
    "summary_creation": "prompts/summary_creation.txt"
  }
}
```

### Modifying Prompts

Simply edit the text files in the `prompts/` directory:

- `prompts/topics_extraction.txt` - Prompt for extracting topics from articles
- `prompts/entities_extraction.txt` - Prompt for extracting named entities
- `prompts/keywords_extraction.txt` - Prompt for extracting keywords
- `prompts/sentiment_analysis.txt` - Prompt for sentiment analysis
- `prompts/summary_creation.txt` - Prompt for creating article summaries

After editing prompts, run `python3 generate-init-sql.py` to regenerate the SQL file.

### Environment Variables

You can override the config file location:

```bash
CONFIG_FILE=/path/to/custom/config.json python3 generate-init-sql.py
```

## Requirements

- `python3` - Python 3.6 or higher

## Notes

- Always run `python3 generate-init-sql.py` after modifying configuration or prompts
- The generated `init.sql` file should not be edited directly
- Vector dimensions are automatically applied to all relevant table columns
- Single quotes in prompts are automatically escaped for SQL compatibility