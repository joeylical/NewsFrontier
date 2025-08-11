#!/usr/bin/env python3
"""
Database management utilities for NewsFrontier
"""

import sys
import click
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

DEFAULT_CONN_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'newsfrontier_db',
    'user': 'newsfrontier',
    'password': 'dev_password'
}

def get_connection(conn_params):
    """Get database connection."""
    try:
        conn = psycopg2.connect(**conn_params)
        return conn
    except psycopg2.Error as e:
        print(f"{Fore.RED}❌ Database connection failed: {e}{Style.RESET_ALL}")
        return None

@click.group()
@click.option('--host', default='localhost', help='Database host')
@click.option('--port', default=5432, help='Database port')
@click.option('--database', default='newsfrontier_db', help='Database name')
@click.option('--user', default='newsfrontier', help='Database user')
@click.option('--password', default='dev_password', help='Database password')
@click.pass_context
def cli(ctx, host, port, database, user, password):
    """NewsFrontier database management utilities."""
    ctx.ensure_object(dict)
    ctx.obj['conn_params'] = {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password
    }

@cli.command()
@click.pass_context
def status(ctx):
    """Check database status and connection."""
    conn_params = ctx.obj['conn_params']
    
    print(f"{Fore.BLUE}🔍 Checking database status...{Style.RESET_ALL}")
    print(f"   Host: {conn_params['host']}:{conn_params['port']}")
    print(f"   Database: {conn_params['database']}")
    print(f"   User: {conn_params['user']}")
    
    conn = get_connection(conn_params)
    if not conn:
        sys.exit(1)
    
    try:
        cur = conn.cursor()
        
        # Check database version
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"{Fore.GREEN}✅ Database connection successful{Style.RESET_ALL}")
        print(f"   Version: {version.split(',')[0]}")
        
        # Check pgvector extension
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        if cur.fetchone():
            print(f"{Fore.GREEN}✅ pgvector extension is installed{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  pgvector extension not found{Style.RESET_ALL}")
        
        # Check tables
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        if tables:
            print(f"\n{Fore.BLUE}📋 Database tables ({len(tables)}):{Style.RESET_ALL}")
            for table in tables:
                print(f"   • {table}")
        else:
            print(f"{Fore.YELLOW}⚠️  No tables found{Style.RESET_ALL}")
            
    except psycopg2.Error as e:
        print(f"{Fore.RED}❌ Database query failed: {e}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        conn.close()

@cli.command()
@click.pass_context
def users(ctx):
    """List all users in the database."""
    conn_params = ctx.obj['conn_params']
    
    conn = get_connection(conn_params)
    if not conn:
        sys.exit(1)
    
    try:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, username, email, is_admin, credits, credits_accrual, 
                   created_at, updated_at 
            FROM users 
            ORDER BY created_at DESC;
        """)
        users = cur.fetchall()
        
        if users:
            print(f"{Fore.BLUE}👥 Users in database ({len(users)}):{Style.RESET_ALL}")
            print(f"   {'ID':<4} {'Username':<15} {'Email':<25} {'Role':<8} {'Credits':<8} {'Created':<12}")
            print(f"   {'-'*4} {'-'*15} {'-'*25} {'-'*8} {'-'*8} {'-'*12}")
            
            for user in users:
                user_id, username, email, is_admin, credits, credits_accrual, created_at, updated_at = user
                role = "Admin" if is_admin else "User"
                role_color = Fore.RED if is_admin else Fore.YELLOW
                created_str = created_at.strftime('%Y-%m-%d') if created_at else 'N/A'
                
                print(f"   {user_id:<4} {Fore.CYAN}{username:<15}{Style.RESET_ALL} "
                      f"{email:<25} {role_color}{role:<8}{Style.RESET_ALL} "
                      f"{credits:<8} {created_str:<12}")
        else:
            print(f"{Fore.YELLOW}⚠️  No users found in database{Style.RESET_ALL}")
            
    except psycopg2.Error as e:
        print(f"{Fore.RED}❌ Database query failed: {e}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        conn.close()

@cli.command()
@click.pass_context
def feeds(ctx):
    """List all RSS feeds in the database."""
    conn_params = ctx.obj['conn_params']
    
    conn = get_connection(conn_params)
    if not conn:
        sys.exit(1)
    
    try:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, uuid, url, title, last_fetch_status, last_fetch_at, 
                   fetch_interval_minutes, created_at
            FROM rss_feeds 
            ORDER BY created_at DESC;
        """)
        feeds = cur.fetchall()
        
        if feeds:
            print(f"{Fore.BLUE}📡 RSS feeds in database ({len(feeds)}):{Style.RESET_ALL}")
            for feed in feeds:
                feed_id, uuid, url, title, status, last_fetch, interval, created = feed
                status_color = Fore.GREEN if status == 'success' else Fore.RED if status == 'failed' else Fore.YELLOW
                print(f"   • {Fore.CYAN}[{feed_id}]{Style.RESET_ALL} {title or 'Untitled'}")
                print(f"     URL: {url}")
                print(f"     Status: {status_color}{status}{Style.RESET_ALL} | "
                      f"Interval: {interval}min | "
                      f"Last Fetch: {last_fetch.strftime('%Y-%m-%d %H:%M') if last_fetch else 'Never'}")
                print()
        else:
            print(f"{Fore.YELLOW}⚠️  No RSS feeds found in database{Style.RESET_ALL}")
            
    except psycopg2.Error as e:
        print(f"{Fore.RED}❌ Database query failed: {e}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        conn.close()

@cli.command()
@click.option('--tables', is_flag=True, help='Drop all tables')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def reset(ctx, tables, confirm):
    """Reset database (drop tables or entire database)."""
    conn_params = ctx.obj['conn_params']
    
    if not confirm:
        action = "drop all tables" if tables else "reset entire database"
        if not click.confirm(f"Are you sure you want to {action}?"):
            print(f"{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
            return
    
    conn = get_connection(conn_params)
    if not conn:
        sys.exit(1)
    
    try:
        cur = conn.cursor()
        
        if tables:
            print(f"{Fore.BLUE}🗑️  Dropping all tables...{Style.RESET_ALL}")
            
            # Get all tables
            cur.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public';
            """)
            table_names = [row[0] for row in cur.fetchall()]
            
            if table_names:
                # Drop tables with CASCADE to handle dependencies
                for table in table_names:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    print(f"   ✓ Dropped table: {table}")
                    
                conn.commit()
                print(f"{Fore.GREEN}✅ All tables dropped successfully{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️  No tables found to drop{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Database reset not implemented yet{Style.RESET_ALL}")
            
    except psycopg2.Error as e:
        print(f"{Fore.RED}❌ Database operation failed: {e}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    cli()