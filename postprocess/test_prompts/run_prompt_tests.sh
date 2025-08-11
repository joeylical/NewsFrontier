#!/usr/bin/env bash

# 测试prompt的便捷Shell脚本
# 使用方法：
#   ./run_prompt_tests.sh summary --sample
#   ./run_prompt_tests.sh cluster --article-id 123
#   ./run_prompt_tests.sh daily --user-id 1 --date 2024-01-15
#   ./run_prompt_tests.sh cover --sample

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export $(grep -v '^#' $PROJECT_ROOT/.env | grep -v '^$' | xargs)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用说明
show_usage() {
    cat << EOF
Usage: $0 <prompt_type> [options]

Prompt Types:
  summary     - Test summary creation prompt
  cluster     - Test cluster detection prompt  
  daily       - Test daily summary prompt
  cover       - Test cover image generation prompt
  all         - Run all prompt tests

Common Options:
  --sample              Use sample data instead of real data
  --config PATH         Path to config file
  --help               Show this help message

Summary Options:
  --article-id ID      Article ID to test with

Cluster Options:
  --article-id ID      Article ID to test with
  --user-id ID         User ID for testing (default: 1)

Daily Summary Options:
  --user-id ID         User ID to test with (default: 1)
  --date YYYY-MM-DD    Date to test (default: yesterday)

Cover Image Options:
  --summary-id ID      Daily summary ID to test with

Examples:
  $0 summary --sample
  $0 summary --article-id 123
  $0 cluster --sample --user-id 1
  $0 cluster --article-id 456 --user-id 2
  $0 daily --sample
  $0 daily --user-id 1 --date 2024-01-15
  $0 cover --sample
  $0 cover --summary-id 789
  $0 all --sample

EOF
}

# 检查uv环境
check_uv_env() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed or not in PATH"
        print_error "Please install uv first: pip install uv"
        exit 1
    fi
    
    # 检查是否在项目根目录
    if [ ! -f "$PROJECT_ROOT/scripts/config.json" ] && [ ! -f "$PROJECT_ROOT/scripts/config.json.example" ]; then
        print_warning "Config file not found in scripts directory: $PROJECT_ROOT/scripts"
        print_warning "Please make sure you're running this script from the correct location"
    fi
}

# 运行单个prompt测试
run_prompt_test() {
    local prompt_type=$1
    shift
    local args=("$@")
    
    local script_path="$SCRIPT_DIR/test_${prompt_type}.py"
    
    if [ ! -f "$script_path" ]; then
        print_error "Test script not found: $script_path"
        return 1
    fi
    
    print_info "Running ${prompt_type} prompt test..."
    echo "Command: uv run $script_path ${args[*]}"
    echo ""
    
    cd "$PROJECT_ROOT/postprocess"
    uv run "${script_path#$PROJECT_ROOT/postprocess/}" "${args[@]}"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "${prompt_type} test completed successfully"
    else
        print_error "${prompt_type} test failed with exit code $exit_code"
    fi
    
    return $exit_code
}

# 运行所有测试
run_all_tests() {
    local args=("$@")
    local failed_tests=()
    
    print_info "Running all prompt tests..."
    echo ""
    
    # 运行摘要测试
    print_info "=== Testing Summary Creation ==="
    if ! run_prompt_test "summary_creation" "${args[@]}"; then
        failed_tests+=("summary_creation")
    fi
    echo ""
    
    # 运行聚类测试
    print_info "=== Testing Cluster Detection ==="
    if ! run_prompt_test "cluster_detection" "${args[@]}"; then
        failed_tests+=("cluster_detection")
    fi
    echo ""
    
    # 运行每日摘要测试
    print_info "=== Testing Daily Summary ==="
    if ! run_prompt_test "daily_summary" "${args[@]}"; then
        failed_tests+=("daily_summary")
    fi
    echo ""
    
    # 运行封面图片测试
    print_info "=== Testing Cover Image Generation ==="
    if ! run_prompt_test "cover_image_generation" "${args[@]}"; then
        failed_tests+=("cover_image_generation")
    fi
    echo ""
    
    # 总结结果
    print_info "=== Test Summary ==="
    if [ ${#failed_tests[@]} -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Failed tests: ${failed_tests[*]}"
        return 1
    fi
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    local prompt_type=$1
    shift
    
    # 处理help选项
    for arg in "$@"; do
        if [ "$arg" = "--help" ] || [ "$arg" = "-h" ]; then
            show_usage
            exit 0
        fi
    done
    
    check_uv_env
    
    case "$prompt_type" in
        summary)
            run_prompt_test "summary_creation" "$@"
            ;;
        cluster)
            run_prompt_test "cluster_detection" "$@"
            ;;
        daily)
            run_prompt_test "daily_summary" "$@"
            ;;
        cover)
            run_prompt_test "cover_image_generation" "$@"
            ;;
        all)
            run_all_tests "$@"
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown prompt type: $prompt_type"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
