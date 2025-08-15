#!/usr/bin/env python3
"""Example usage of the simplified dependency factory."""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.utils import get_simple_factory
from domain.exceptions import LLMConnectionError, ReportAnalysisError


def example_pdf_analysis():
    """Example: Analyze a PDF document."""
    print("=== PDF Analysis Example ===")
    
    # Get factory instance
    factory = get_simple_factory()
    
    try:
        # Create PDF reading use case with specific model
        pdf_use_case = factory.create_read_pdf_use_case(
            provider="openai",
            model_name="gpt-3.5-turbo",
            temperature=0.1
        )
        
        # Example PDF path (replace with actual path)
        pdf_path = "example_report.pdf"
        
        if os.path.exists(pdf_path):
            result = pdf_use_case.execute(pdf_path)
            print(f"Analysis completed: {result.summary[:100]}...")
        else:
            print(f"PDF file not found: {pdf_path}")
            
    except LLMConnectionError as e:
        print(f"LLM connection error: {e}")
    except ReportAnalysisError as e:
        print(f"Analysis error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def example_triage_analysis():
    """Example: Perform vulnerability triage."""
    print("\n=== Triage Analysis Example ===")
    
    factory = get_simple_factory()
    
    try:
        # Create triage use case
        triage_use_case = factory.create_triage_use_case(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229"
        )
        
        # Example security report data
        report_data = {
            "vulnerabilities": [
                {
                    "id": "CVE-2023-1234",
                    "severity": "HIGH",
                    "description": "SQL Injection vulnerability",
                    "component": "web-app"
                },
                {
                    "id": "CVE-2023-5678",
                    "severity": "MEDIUM",
                    "description": "Cross-site scripting",
                    "component": "frontend"
                }
            ]
        }
        
        result = triage_use_case.execute(report_data)
        print(f"Triage completed. Priority vulnerabilities: {len(result.high_priority)}")
        
    except Exception as e:
        print(f"Triage error: {e}")


def example_complete_analysis():
    """Example: Run complete security analysis."""
    print("\n=== Complete Analysis Example ===")
    
    factory = get_simple_factory()
    
    try:
        # Create complete analysis use case
        complete_use_case = factory.create_complete_analysis_use_case(
            provider="openai",
            temperature=0.2
        )
        
        # Example paths
        pdf_path = "security_report.pdf"
        target_path = "/path/to/source/code"
        
        if os.path.exists(pdf_path) and os.path.exists(target_path):
            result = complete_use_case.execute(pdf_path, target_path)
            print(f"Complete analysis finished. Total findings: {len(result.all_findings)}")
        else:
            print("Required files/directories not found for complete analysis")
            
    except Exception as e:
        print(f"Complete analysis error: {e}")


def example_factory_utilities():
    """Example: Use factory utility methods."""
    print("\n=== Factory Utilities Example ===")
    
    factory = get_simple_factory()
    
    # Check available providers
    providers = factory.get_available_providers()
    print(f"Available LLM providers: {providers}")
    
    # Validate specific providers
    for provider in ["openai", "anthropic", "google", "ollama"]:
        is_valid = factory.validate_provider(provider)
        status = "✓" if is_valid else "✗"
        print(f"{status} {provider}: {'configured' if is_valid else 'not configured'}")
    
    # Clear cache (useful for testing or memory management)
    factory.clear_cache()
    print("LLM cache cleared")


def example_direct_component_creation():
    """Example: Create individual components directly."""
    print("\n=== Direct Component Creation Example ===")
    
    factory = get_simple_factory()
    
    # Create individual components
    pdf_reader = factory.create_pdf_reader()
    print(f"PDF Reader created: {type(pdf_reader).__name__}")
    
    try:
        llm = factory.create_llm(provider="openai", temperature=0.1)
        print(f"LLM created: {type(llm).__name__}")
        
        security_analyzer = factory.create_security_analyzer(llm)
        print(f"Security Analyzer created: {type(security_analyzer).__name__}")
        
        triage_analyzer = factory.create_triage_analyzer(llm)
        print(f"Triage Analyzer created: {type(triage_analyzer).__name__}")
        
        static_analyzer = factory.create_static_analyzer(llm=llm)
        print(f"Static Analyzer created: {type(static_analyzer).__name__}")
        
    except Exception as e:
        print(f"Component creation error: {e}")


if __name__ == "__main__":
    print("Simplified Factory Usage Examples")
    print("=" * 40)
    
    # Run examples
    example_factory_utilities()
    example_direct_component_creation()
    example_pdf_analysis()
    example_triage_analysis()
    example_complete_analysis()
    
    print("\n=== Examples completed ===")
    print("\nNote: Make sure to:")
    print("1. Set up your LLM API keys in environment variables")
    print("2. Have actual PDF files and source code for testing")
    print("3. Install all required dependencies")