"""
LLM Sandbox Constants and Types
Local implementation based on llm-sandbox MCP server constants
"""

from enum import Enum
from typing import Dict, Any, List

class SupportedLanguage(str, Enum):
    """Supported programming languages matching llm-sandbox MCP server."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUBY = "ruby"
    R = "r"
    JULIA = "julia"

# Language resources configuration - matching official llm-sandbox
LANGUAGE_RESOURCES = {
    SupportedLanguage.PYTHON: {
        "version": "3.11",
        "package_manager": "pip",
        "preinstalled_libraries": [
            "numpy", "pandas", "matplotlib", "pillow", "seaborn",
            "scikit-learn", "scipy", "scikit-image", "plotly"
        ],
        "use_cases": [
            "Data science", "Web development", "Automation", "Machine learning"
        ],
        "visualization_support": True,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple Python hello world program",
                "code": "print('Hello, World!')"
            },
            {
                "title": "Data Analysis with Pandas",
                "description": "Basic data analysis using pandas",
                "code": """import pandas as pd
import numpy as np

# Create sample data
data = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'score': [85, 92, 78, 96]
})

print("Dataset:")
print(data)
print("\\nAverage score:", data['score'].mean())"""
            },
            {
                "title": "Data Visualization",
                "description": "Creating plots with matplotlib",
                "code": """import matplotlib.pyplot as plt
import numpy as np

# Generate data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(x, y1, label='sin(x)', linewidth=2)
plt.plot(x, y2, label='cos(x)', linewidth=2)
plt.title('Trigonometric Functions')
plt.xlabel('x')
plt.ylabel('y')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()"""
            }
        ]
    },
    SupportedLanguage.JAVASCRIPT: {
        "version": "18.x",
        "package_manager": "npm",
        "preinstalled_libraries": ["lodash", "moment", "axios"],
        "use_cases": ["Web development", "Node.js applications", "Automation"],
        "visualization_support": False,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple JavaScript hello world program",
                "code": "console.log('Hello, World!');"
            }
        ]
    },
    SupportedLanguage.JAVA: {
        "version": "17",
        "package_manager": "maven",
        "preinstalled_libraries": ["junit", "slf4j"],
        "use_cases": ["Enterprise applications", "Android development", "Backend services"],
        "visualization_support": False,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple Java hello world program",
                "code": """public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}"""
            }
        ]
    },
    SupportedLanguage.CPP: {
        "version": "20",
        "package_manager": "conan",
        "preinstalled_libraries": ["boost", "eigen"],
        "use_cases": ["System programming", "Game development", "High-performance computing"],
        "visualization_support": False,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple C++ hello world program",
                "code": """#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}"""
            }
        ]
    },
    SupportedLanguage.GO: {
        "version": "1.21",
        "package_manager": "go mod",
        "preinstalled_libraries": ["fmt", "net/http"],
        "use_cases": ["Web services", "CLI tools", "Microservices"],
        "visualization_support": False,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple Go hello world program",
                "code": """package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}"""
            }
        ]
    },
    SupportedLanguage.RUBY: {
        "version": "3.2",
        "package_manager": "gem",
        "preinstalled_libraries": ["rails", "sinatra"],
        "use_cases": ["Web development", "Automation", "Scripting"],
        "visualization_support": False,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple Ruby hello world program",
                "code": "puts 'Hello, World!'"
            }
        ]
    },
    SupportedLanguage.R: {
        "version": "4.3",
        "package_manager": "cran",
        "preinstalled_libraries": ["ggplot2", "dplyr", "tidyr", "shiny"],
        "use_cases": ["Statistical analysis", "Data visualization", "Research"],
        "visualization_support": True,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple R hello world program",
                "code": "cat('Hello, World!\\n')"
            },
            {
                "title": "Data Visualization",
                "description": "Creating plots with ggplot2",
                "code": """library(ggplot2)

# Create sample data
data <- data.frame(
  x = 1:10,
  y = rnorm(10)
)

# Create plot
ggplot(data, aes(x = x, y = y)) +
  geom_point() +
  geom_line() +
  labs(title = "Sample Data Plot", x = "X", y = "Y") +
  theme_minimal()"""
            }
        ]
    },
    SupportedLanguage.JULIA: {
        "version": "1.9",
        "package_manager": "pkg",
        "preinstalled_libraries": ["Plots", "DataFrames", "JuMP"],
        "use_cases": ["Scientific computing", "Machine learning", "Optimization"],
        "visualization_support": True,
        "examples": [
            {
                "title": "Hello World",
                "description": "Simple Julia hello world program",
                "code": "println(\"Hello, World!\")"
            }
        ]
    }
}

# MCP Content Types - matching official llm-sandbox
class ContentType(str, Enum):
    """MCP content types."""
    TEXT = "text"
    IMAGE = "image"
    EMBEDDING = "embedding"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

# Execution Result Types - matching official llm-sandbox
class ExecutionResult:
    """Execution result from sandbox."""
    def __init__(self, exit_code: int, stdout: str = "", stderr: str = "", execution_time: float = None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.plots = []  # For visualization support
    
    def to_json(self, include_plots: bool = True) -> str:
        """Convert to JSON string."""
        import json
        data = {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time": self.execution_time
        }
        if include_plots and self.plots:
            data["plots"] = self.plots
        return json.dumps(data, indent=2)