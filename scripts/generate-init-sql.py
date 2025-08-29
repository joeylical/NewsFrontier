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
        
        llm_models_config = config['llm_models']
        features_config = config['features']
        processing_config = config['processing']
        storage_config = config['storage']
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
    print(f"  - LLM models configured: {len(llm_models_config)}")
    for model in llm_models_config:
        status = "active" if model['is_active'] else "inactive"
        print(f"    • {model['name']} ({model['model_type']}): {model['model_name']} [{status}]")
    print(f"  - Daily summary enabled: {features_config['daily_summary_enabled']}")
    print(f"  - Scraper interval: {processing_config['scraper_interval_minutes']} minutes")
    print(f"  - Batch processing enabled: {processing_config['batch_processing_enabled']}")
    print(f"  - S3 region: {storage_config['s3_region']}")
    
    # Function to read prompt content and convert to YAML format if needed
    def read_prompt(prompt_file, prompt_name):
        full_path = script_dir / prompt_file
        
        if not full_path.exists():
            print(f"Error: Prompt file not found: {full_path}")
            sys.exit(1)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Check file extension
            file_ext = full_path.suffix.lower()
            
            if file_ext == '.txt':
                # Convert TXT to YAML format
                # Create a proper name from the prompt key
                formatted_name = prompt_name.replace('_', ' ').title()
                
                yaml_content = f"""name: {formatted_name}
description: Generated from {prompt_file}
stages:
  - name: main_prompt
    type: final
    prompt: |
{chr(10).join('      ' + line for line in content.split(chr(10)))}"""
                
                print(f"  - Converted {prompt_file} (TXT) to YAML format")
                # Escape single quotes for SQL
                return yaml_content.replace("'", "''")
                
            elif file_ext in ['.yaml', '.yml']:
                # Use YAML content as-is
                print(f"  - Using {prompt_file} (YAML) as-is")
                # Escape single quotes for SQL  
                return content.replace("'", "''")
            else:
                print(f"Error: Unsupported file format: {file_ext} for {prompt_file}")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error reading prompt file {full_path}: {e}")
            sys.exit(1)
    
    print("Loading prompts from modular files...")
    
    # Read prompt files and convert to YAML format if needed
    try:
        prompts = {}
        for key, filename in prompts_config.items():
            prompts[f'PROMPT_{key.upper()}_YAML'] = read_prompt(filename, key)
    except Exception as e:
        print(f"Error loading prompts: {e}")
        sys.exit(1)
    
    # Function to generate LLM model INSERT statements
    def generate_llm_models_sql(models):
        insert_statements = []
        for model in models:
            # Convert boolean values to SQL format
            is_active = 'true' if model['is_active'] else 'false'
            
            # Escape single quotes in strings for SQL
            name = model['name'].replace("'", "''")
            model_type = model['model_type'].replace("'", "''")
            provider = model['provider'].replace("'", "''")
            model_name = model['model_name'].replace("'", "''")
            description = model.get('description', '').replace("'", "''")
            
            # Optional fields
            api_base_url = model.get('api_base_url')
            config_json = model.get('config_json')
            
            api_base_url_sql = f"'{api_base_url.replace(chr(39), chr(39)+chr(39))}'" if api_base_url else 'NULL'
            config_json_sql = f"'{config_json.replace(chr(39), chr(39)+chr(39))}'" if config_json else 'NULL'
            
            insert_stmt = f"""    ('{name}', '{model_type}', '{provider}', '{model_name}', NULL, {api_base_url_sql}, {is_active}, {config_json_sql}, '{description}')"""
            insert_statements.append(insert_stmt)
        
        return ',\n'.join(insert_statements)
    
    print("Generating LLM models SQL...")
    llm_models_sql = generate_llm_models_sql(llm_models_config)
    
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
        # Database configuration
        'EMBEDDING_DIMENSION': str(embedding_dimension),
        'DEFAULT_RSS_FETCH_INTERVAL': str(default_rss_fetch_interval),
        'MAX_PROCESSING_ATTEMPTS': str(max_processing_attempts),
        'SIMILARITY_THRESHOLD': str(similarity_threshold),
        'CLUSTER_THRESHOLD': str(cluster_threshold),
        'MAX_ARTICLES_PER_EVENT': str(max_articles_per_event),
        
        # LLM Models configuration
        'LLM_MODELS_INSERT_DATA': llm_models_sql,
        
        # Features configuration
        'DAILY_SUMMARY_ENABLED': features_config['daily_summary_enabled'],
        'DAILY_SUMMARY_COVER_ENABLED': features_config['daily_summary_cover_enabled'],
        
        # Processing configuration
        'SCRAPER_INTERVAL_MINUTES': str(processing_config['scraper_interval_minutes']),
        'POSTPROCESS_INTERVAL_MINUTES': str(processing_config['postprocess_interval_minutes']),
        'MAX_ARTICLE_AGE_DAYS': str(processing_config['max_article_age_days']),
        'BATCH_PROCESSING_SIZE': str(processing_config['batch_processing_size']),
        'BATCH_PROCESSING_ENABLED': processing_config['batch_processing_enabled'],
        
        # Storage configuration
        'S3_REGION': storage_config['s3_region'],
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