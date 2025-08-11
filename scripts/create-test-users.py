#!/usr/bin/env python3
"""
Create test users for NewsFrontier development environment
"""

import sys
import click
import psycopg2
from passlib.context import CryptContext
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Password hashing context (same as backend)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_users(conn_params=None):
    """Create admin and test users in the database."""
    
    # Default database connection parameters
    if conn_params is None:
        conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'newsfrontier_db',
            'user': 'newsfrontier',
            'password': 'dev_password'
        }
    
    try:
        # Connect to database
        print(f"{Fore.BLUE}Connecting to database...{Style.RESET_ALL}")
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Hash passwords
        admin_password_hash = pwd_context.hash("admin")
        test_password_hash = pwd_context.hash("test")
        
        print(f"{Fore.BLUE}Creating test users...{Style.RESET_ALL}")
        
        # Create admin user
        cur.execute("""
            INSERT INTO users (username, password_hash, email, is_admin, credits, credits_accrual) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                email = EXCLUDED.email,
                is_admin = EXCLUDED.is_admin,
                updated_at = NOW()
        """, ('admin', admin_password_hash, 'admin@newsfrontier.dev', True, 1000, 100))
        
        # Create test user
        cur.execute("""
            INSERT INTO users (username, password_hash, email, is_admin, credits, credits_accrual) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                email = EXCLUDED.email,
                is_admin = EXCLUDED.is_admin,
                updated_at = NOW()
        """, ('test', test_password_hash, 'test@newsfrontier.dev', False, 500, 50))
        
        # Commit changes
        conn.commit()
        
        print(f"{Fore.GREEN}✅ Test users created successfully:{Style.RESET_ALL}")
        print(f"   • {Fore.CYAN}admin/admin{Style.RESET_ALL} (Administrator)")
        print(f"   • {Fore.CYAN}test/test{Style.RESET_ALL} (Regular User)")
        
        # Verify users were created
        cur.execute("SELECT username, email, is_admin, credits FROM users WHERE username IN ('admin', 'test')")
        users = cur.fetchall()
        
        print(f"\n{Fore.BLUE}📋 User Details:{Style.RESET_ALL}")
        for user in users:
            username, email, is_admin, credits = user
            role = "Admin" if is_admin else "User"
            role_color = Fore.RED if is_admin else Fore.YELLOW
            print(f"   • {Fore.CYAN}{username}{Style.RESET_ALL}: {email} ({role_color}{role}{Style.RESET_ALL}, {credits} credits)")
            
    except psycopg2.Error as e:
        print(f"{Fore.RED}❌ Database error: {e}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            
    return True

@click.command()
@click.option('--host', default='localhost', help='Database host')
@click.option('--port', default=5432, help='Database port')
@click.option('--database', default='newsfrontier_db', help='Database name')
@click.option('--user', default='newsfrontier', help='Database user')
@click.option('--password', default='dev_password', help='Database password')
def main(host, port, database, user, password):
    """Create test users for NewsFrontier development environment."""
    # Create connection parameters from CLI options
    conn_params = {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password
    }
    
    success = create_test_users(conn_params)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()