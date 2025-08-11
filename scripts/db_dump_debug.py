#!/usr/bin/env python3
"""
数据库调试脚本 - dump数据用于调试

功能：
1. 导出 rss_feeds, rss_subscriptions, rss_fetch_records, rss_items_metadata 四个表的数据
2. 默认在导出的数据中将 rss_items_metadata 表的 processing_status 修改为 'pending'
3. 使用 --derivative 选项时，额外导出 rss_item_derivatives 表，且不重置 processing_status
4. 生成可以重新导入的SQL文件

使用方法：
python db_dump_debug.py [--output-dir DIR] [--derivative]

选项：
  --output-dir DIR    输出目录 (默认: ./debug_dump)
  --derivative        包含 derivatives 表并保持原始 processing_status
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor


def get_database_url() -> str:
    """获取数据库连接URL"""
    return os.getenv(
        "DATABASE_URL", 
        "postgresql://newsfrontier:dev_password@localhost:5432/newsfrontier_db"
    )


def create_db_connection():
    """创建数据库连接"""
    db_url = get_database_url()
    # 解析数据库URL
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/'),
        user=parsed.username,
        password=parsed.password
    )


def export_table_data(cursor, table_name: str) -> List[Dict[str, Any]]:
    """导出指定表的所有数据"""
    print(f"正在导出表: {table_name}")
    
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        row_dict = {}
        for i, value in enumerate(row):
            # 处理特殊类型
            if isinstance(value, datetime):
                row_dict[columns[i]] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                row_dict[columns[i]] = str(value)
            elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                # 处理数组/向量类型
                row_dict[columns[i]] = list(value) if value else None
            else:
                row_dict[columns[i]] = value
        data.append(row_dict)
    
    print(f"  导出了 {len(data)} 条记录")
    return data


def reset_processing_status_in_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """在导出的数据中重置processing_status为pending"""
    reset_count = 0
    for row in data:
        if row.get('processing_status') != 'pending':
            row['processing_status'] = 'pending'
            row['processing_started_at'] = None
            row['processing_completed_at'] = None
            row['processing_attempts'] = 0
            row['last_error_message'] = None
            reset_count += 1
    
    print(f"  在导出数据中重置了 {reset_count} 条记录的处理状态为 pending")
    return data


def format_sql_value(value):
    """格式化SQL值"""
    if value is None:
        return "NULL"
    elif isinstance(value, str):
        # 转义单引号和反斜杠
        escaped = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{escaped}'"
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    elif isinstance(value, list):
        # 处理数组类型（如vector）
        if value:
            array_str = "{" + ",".join(str(v) for v in value) + "}"
            return f"'{array_str}'"
        else:
            return "NULL"
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        return f"'{str(value)}'"


def generate_insert_sql(table_name: str, data: List[Dict[str, Any]]) -> str:
    """生成INSERT SQL语句"""
    if not data:
        return f"-- 表 {table_name} 无数据\n\n"
    
    # 获取所有列名
    columns = list(data[0].keys())
    
    sql_lines = [
        f"-- 导入 {table_name} 表数据",
        f"-- 记录数: {len(data)}",
        f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;",
        ""
    ]
    
    # 批量插入，每批100条
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        # 构建INSERT语句
        columns_str = ", ".join(f'"{col}"' for col in columns)
        
        values_list = []
        for row in batch:
            values = [format_sql_value(row[col]) for col in columns]
            values_str = "(" + ", ".join(values) + ")"
            values_list.append(values_str)
        
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES\n"
        insert_sql += ",\n".join(values_list) + ";\n"
        sql_lines.append(insert_sql)
    
    return "\n".join(sql_lines) + "\n\n"


def main():
    parser = argparse.ArgumentParser(description="数据库调试脚本 - dump数据用于调试")
    parser.add_argument("--output-dir", default="./debug_dump", help="输出目录")
    parser.add_argument("--derivative", action="store_true", 
                       help="包含 derivatives 表并保持原始 processing_status")
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 要导出的表（按依赖关系排序）
    tables_to_export = ["rss_feeds", "rss_subscriptions", "rss_fetch_records", "rss_items_metadata"]
    if args.derivative:
        tables_to_export.append("rss_item_derivatives")
    
    try:
        conn = create_db_connection()
        cursor = conn.cursor()
        
        exported_data = {}
        
        print("开始导出数据...")
        for table_name in tables_to_export:
            data = export_table_data(cursor, table_name)
            
            # 如果是rss_items_metadata表，且没有使用--derivative选项，重置processing_status
            if table_name == "rss_items_metadata" and not args.derivative:
                data = reset_processing_status_in_data(data)
            
            exported_data[table_name] = data
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成JSON文件（便于调试查看）
        json_file = output_dir / f"debug_dump_{timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"JSON数据已保存到: {json_file}")
        
        # 生成SQL文件
        mode_suffix = "_with_derivatives" if args.derivative else "_reset_pending"
        sql_file = output_dir / f"debug_restore_{timestamp}{mode_suffix}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- 数据库调试数据恢复脚本\n")
            f.write(f"-- 生成时间: {datetime.now()}\n")
            if args.derivative:
                f.write("-- 模式: 包含 derivatives 表，保持原始 processing_status\n")
            else:
                f.write("-- 模式: 基础表，processing_status 重置为 pending\n")
            f.write("-- 使用方法: psql -h localhost -U newsfrontier -d newsfrontier_db -f debug_restore.sql\n")
            f.write("-- 或者在dev.sh中使用: ./dev.sh full-cleanup --restore-debug\n\n")
            
            f.write("SET client_encoding = 'UTF8';\n")
            f.write("SET standard_conforming_strings = on;\n")
            f.write("SET check_function_bodies = false;\n")
            f.write("SET xmloption = content;\n")
            f.write("SET client_min_messages = warning;\n\n")
            
            f.write("BEGIN;\n\n")
            
            # 按依赖关系顺序导入
            for table_name in tables_to_export:
                if table_name in exported_data:
                    f.write(generate_insert_sql(table_name, exported_data[table_name]))
            
            f.write("COMMIT;\n")
        
        print(f"SQL恢复脚本已保存到: {sql_file}")
        
        # 创建最新的软链接，方便dev.sh使用
        latest_sql = output_dir / "latest_debug_restore.sql"
        if latest_sql.exists():
            latest_sql.unlink()
        latest_sql.symlink_to(sql_file.name)
        
        print(f"最新恢复脚本软链接: {latest_sql}")
        
        # 生成统计信息
        stats = {}
        total_records = 0
        for table_name, data in exported_data.items():
            count = len(data)
            stats[table_name] = count
            total_records += count
        
        mode_suffix = "_with_derivatives" if args.derivative else "_reset_pending"
        stats_file = output_dir / f"dump_stats_{timestamp}{mode_suffix}.txt"
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(f"数据导出统计 - {datetime.now()}\n")
            if args.derivative:
                f.write("导出模式: 包含 derivatives 表，保持原始 processing_status\n")
            else:
                f.write("导出模式: 基础表，processing_status 重置为 pending\n")
            f.write("=" * 50 + "\n\n")
            for table_name, count in stats.items():
                f.write(f"{table_name}: {count} 条记录\n")
            f.write(f"\n总计: {total_records} 条记录\n")
            
            if 'rss_items_metadata' in exported_data:
                # 统计processing_status分布
                status_counts = {}
                for row in exported_data['rss_items_metadata']:
                    status = row.get('processing_status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                f.write(f"\nrss_items_metadata处理状态分布:\n")
                for status, count in status_counts.items():
                    f.write(f"  {status}: {count}\n")
            
            if 'rss_item_derivatives' in exported_data:
                # 统计derivatives处理状态分布
                deriv_status_counts = {}
                for row in exported_data['rss_item_derivatives']:
                    status = row.get('processing_status', 'unknown')
                    deriv_status_counts[status] = deriv_status_counts.get(status, 0) + 1
                
                f.write(f"\nrss_item_derivatives处理状态分布:\n")
                for status, count in deriv_status_counts.items():
                    f.write(f"  {status}: {count}\n")
        
        print(f"统计信息已保存到: {stats_file}")
        print(f"\n导出完成! 总计 {total_records} 条记录")
        
        if args.derivative:
            print("导出模式: 包含 rss_item_derivatives 表，保持原始 processing_status")
            if 'rss_item_derivatives' in exported_data:
                print(f"rss_item_derivatives表: {len(exported_data['rss_item_derivatives'])} 条记录")
        else:
            print("导出模式: 基础表，rss_items_metadata 的 processing_status 已重置为 pending")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()