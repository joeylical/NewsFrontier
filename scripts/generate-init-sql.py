#!/usr/bin/env python3

"""
Generate init.sql from template with configuration file substitution
This script reads config.json and prompt files to generate the final init.sql
"""

import json
import os
import sys
from pathlib import Path

def main():
    # Get the script directory
    script_dir = Path(__file__).parent.absolute()
    
    # Configuration file path
    config_file = os.environ.get('CONFIG_FILE', script_dir / 'config.json')
    
    print(f"Reading configuration from: {config_file}")
    
    # Check if config file exists
    if not Path(config_file).exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
    
    # Load configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)
    
    # Read configuration values
    try:
        db_config = config['database']
        embedding_dimension = db_config['embedding_dimension']
        default_rss_fetch_interval = db_config['default_rss_fetch_interval']
        max_processing_attempts = db_config['max_processing_attempts']
        similarity_threshold = db_config['similarity_threshold']
        cluster_threshold = db_config['cluster_threshold']
        max_articles_per_event = db_config['max_articles_per_event']
        
        prompts_config = config['prompts']
    except KeyError as e:
        print(f"Error: Missing configuration key: {e}")
        sys.exit(1)
    
    print("Generating init.sql with configuration:")
    print(f"  - Embedding dimension: {embedding_dimension}")
    print(f"  - RSS fetch interval: {default_rss_fetch_interval} minutes")
    print(f"  - Max processing attempts: {max_processing_attempts}")
    print(f"  - Similarity threshold: {similarity_threshold}")
    print(f"  - Cluster threshold: {cluster_threshold}")
    print(f"  - Max articles per event: {max_articles_per_event}")
    
    # Function to read and escape prompt content for SQL
    def read_prompt(prompt_file):
        full_path = script_dir / prompt_file
        
        if not full_path.exists():
            print(f"Error: Prompt file not found: {full_path}")
            sys.exit(1)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Escape single quotes for SQL
            return content.replace("'", "''")
        except Exception as e:
            print(f"Error reading prompt file {full_path}: {e}")
            sys.exit(1)
    
    print("Loading prompts from modular files...")
    
    # Read prompt files
    try:
        prompts = {}
        for key, filename in prompts_config.items():
            prompts[f'PROMPT_{key.upper()}'] = read_prompt(filename)
    except Exception as e:
        print(f"Error loading prompts: {e}")
        sys.exit(1)
    
    # Read the SQL template
    template_file = script_dir / 'init.sql.template'
    if not template_file.exists():
        print(f"Error: Template file not found: {template_file}")
        sys.exit(1)
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"Error reading template file: {e}")
        sys.exit(1)
    
    # Replace placeholders
    replacements = {
        'EMBEDDING_DIMENSION': str(embedding_dimension),
        'DEFAULT_RSS_FETCH_INTERVAL': str(default_rss_fetch_interval),
        'MAX_PROCESSING_ATTEMPTS': str(max_processing_attempts),
        'SIMILARITY_THRESHOLD': str(similarity_threshold),
        'CLUSTER_THRESHOLD': str(cluster_threshold),
        'MAX_ARTICLES_PER_EVENT': str(max_articles_per_event),
    }
    
    # Add prompts to replacements
    replacements.update(prompts)
    
    # Replace all placeholders
    for key, value in replacements.items():
        placeholder = f'{{{{{key}}}}}'
        sql_content = sql_content.replace(placeholder, value)
    
    # Write the output file
    output_file = script_dir / 'init.sql'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql_content)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)
    
    print(f"Generated {output_file} successfully")

if __name__ == '__main__':
    main()