#!/bin/bash
# demo_langs.sh - Language Runtime Verification Script
# Demonstrates execution of Python, C++, JavaScript, and C# in the multi-language Docker container
# Following :ScriptingPattern for :LanguageRuntimeExecution in :ContainerizationContext

# Text formatting for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner function for visual separation
print_banner() {
    echo -e "\n${BLUE}========== $1 ==========${NC}\n"
}

# Error handling function
handle_error() {
    echo -e "${RED}ERROR: $1${NC}"
    echo -e "${RED}Failed to $2${NC}"
    exit_code=$3
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}Exit code: $exit_code${NC}"
    fi
}

# Success indicator function
print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Create working directory for test files
setup_environment() {
    print_banner "Setting up test environment"
    
    # Create directory for test files if it doesn't exist
    mkdir -p /app/lang_tests
    cd /app/lang_tests
    
    # Clean up any previous test files
    rm -f hello_python.py hello_cpp.cpp hello_js.js HelloCSharp.cs HelloCSharp
    rm -rf HelloCSharp_project
    
    echo "Working directory: $(pwd)"
    print_success "Environment set up"
}

# Test Python runtime
test_python() {
    print_banner "Testing Python Runtime"
    
    echo "Creating Python test file..."
    cat > hello_python.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Python Hello World demo
"""

def main():
    """Print a greeting message"""
    print("Hello from Python!")
    print("Python runtime test: SUCCESS")
    return 0

if __name__ == "__main__":
    main()
EOF
    
    echo "Running Python test..."
    python hello_python.py
    
    if [ $? -eq 0 ]; then
        print_success "Python runtime verification complete"
    else
        handle_error "Python test failed" "execute Python code" $?
        return 1
    fi
    
    return 0
}

# Test C++ runtime
test_cpp() {
    print_banner "Testing C++ Runtime"
    
    echo "Creating C++ test file..."
    cat > hello_cpp.cpp << 'EOF'
#include <iostream>

/**
 * Simple C++ Hello World demo
 */
int main() {
    std::cout << "Hello from C++!" << std::endl;
    std::cout << "C++ runtime test: SUCCESS" << std::endl;
    return 0;
}
EOF
    
    echo "Compiling C++ code..."
    g++ -o hello_cpp hello_cpp.cpp
    
    if [ $? -ne 0 ]; then
        handle_error "C++ compilation failed" "compile C++ code" $?
        return 1
    fi
    
    echo "Running C++ executable..."
    ./hello_cpp
    
    if [ $? -eq 0 ]; then
        print_success "C++ runtime verification complete"
    else
        handle_error "C++ test failed" "execute C++ code" $?
        return 1
    fi
    
    return 0
}

# Test JavaScript (Node.js) runtime
test_javascript() {
    print_banner "Testing JavaScript Runtime"
    
    echo "Creating JavaScript test file..."
    cat > hello_js.js << 'EOF'
/**
 * Simple JavaScript Hello World demo
 */
function main() {
    console.log("Hello from JavaScript!");
    console.log("JavaScript runtime test: SUCCESS");
    return 0;
}

main();
EOF
    
    echo "Running JavaScript test..."
    node hello_js.js
    
    if [ $? -eq 0 ]; then
        print_success "JavaScript runtime verification complete"
    else
        handle_error "JavaScript test failed" "execute JavaScript code" $?
        return 1
    fi
    
    return 0
}

# Test C# runtime
test_csharp() {
    print_banner "Testing C# Runtime"
    
    echo "Creating C# test file..."
    cat > HelloCSharp.cs << 'EOF'
using System;

/**
 * Simple C# Hello World demo
 */
namespace HelloWorld
{
    class Program
    {
        static int Main(string[] args)
        {
            Console.WriteLine("Hello from C#!");
            Console.WriteLine("C# runtime test: SUCCESS");
            return 0;
        }
    }
}
EOF
    
    echo "Creating C# project..."
    mkdir -p HelloCSharp_project
    cd HelloCSharp_project
    
    # Initialize a new console application
    dotnet new console -n HelloCSharp -o .
    
    if [ $? -ne 0 ]; then
        handle_error "C# project creation failed" "create C# project" $?
        return 1
    fi
    
    # Replace the generated Program.cs with our test file
    cp ../HelloCSharp.cs Program.cs
    
    echo "Building C# project..."
    dotnet build
    
    if [ $? -ne 0 ]; then
        handle_error "C# compilation failed" "compile C# code" $?
        return 1
    fi
    
    echo "Running C# application..."
    dotnet run
    
    if [ $? -eq 0 ]; then
        print_success "C# runtime verification complete"
        cd ..
    else
        handle_error "C# test failed" "execute C# code" $?
        cd ..
        return 1
    fi
    
    return 0
}

# Main execution function
main() {
    print_banner "LANGUAGE RUNTIME VERIFICATION"
    echo -e "${YELLOW}This script will test all language runtimes in the container${NC}"
    
    setup_environment
    
    # Track overall success
    overall_success=true
    
    # Test each language runtime, capturing any failures
    if ! test_python; then
        overall_success=false
    fi
    
    if ! test_cpp; then
        overall_success=false
    fi
    
    if ! test_javascript; then
        overall_success=false
    fi
    
    if ! test_csharp; then
        overall_success=false
    fi
    
    # Final status report
    print_banner "VERIFICATION SUMMARY"
    
    if $overall_success; then
        echo -e "${GREEN}✓ All language runtimes verified successfully${NC}"
        echo -e "${GREEN}✓ Container is ready for multi-language development${NC}"
    else
        echo -e "${RED}✗ Some language runtime tests failed${NC}"
        echo -e "${RED}✗ Please check the output above for details${NC}"
        exit 1
    fi
    
    return 0
}

# Execute main function
main