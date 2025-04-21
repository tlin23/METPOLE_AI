#!/usr/bin/env python3
"""
Test script for verifying the deployment of MetPol AI.
This script tests the end-to-end flow including:
- Backend API connectivity
- Crawling functionality
- Querying and asking questions
- Source display
- Feedback logging
"""

import argparse
import requests
import json
import sys
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

console = Console()

def test_backend_connectivity(base_url):
    """Test basic connectivity to the backend API."""
    console.print("\n[bold blue]Testing Backend Connectivity[/bold blue]")
    
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            console.print("[green]✓ Backend is reachable[/green]")
            return True
        else:
            console.print(f"[red]✗ Backend returned status code {response.status_code}[/red]")
            return False
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Failed to connect to backend: {str(e)}[/red]")
        return False

def test_api_endpoints(base_url):
    """Test the API endpoints."""
    console.print("\n[bold blue]Testing API Endpoints[/bold blue]")
    
    endpoints = [
        {"path": "/api/ask", "method": "POST", "data": {"question": "What is Metropole?", "top_k": 3}},
        {"path": "/api/query", "method": "POST", "data": {"query": "building rules", "n_results": 3}}
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"{base_url}{endpoint['path']}")
            else:
                response = requests.post(f"{base_url}{endpoint['path']}", json=endpoint["data"])
            
            if response.status_code in [200, 201]:
                console.print(f"[green]✓ {endpoint['path']} ({endpoint['method']}) - Success[/green]")
                results.append({"endpoint": endpoint, "success": True, "response": response.json()})
            else:
                console.print(f"[red]✗ {endpoint['path']} ({endpoint['method']}) - Failed with status {response.status_code}[/red]")
                results.append({"endpoint": endpoint, "success": False, "status_code": response.status_code})
        except requests.exceptions.RequestException as e:
            console.print(f"[red]✗ {endpoint['path']} ({endpoint['method']}) - Error: {str(e)}[/red]")
            results.append({"endpoint": endpoint, "success": False, "error": str(e)})
    
    return results

def test_crawl_functionality(base_url):
    """Test the crawling functionality."""
    console.print("\n[bold blue]Testing Crawl Functionality[/bold blue]")
    
    try:
        with Progress() as progress:
            task = progress.add_task("[cyan]Crawling...", total=100)
            
            # Start the crawl
            response = requests.post(f"{base_url}/api/crawl", json={"url": "https://www.metropoleballard.com/home"})
            
            if response.status_code in [200, 201]:
                progress.update(task, completed=50)
                data = response.json()
                
                if data.get("success"):
                    progress.update(task, completed=100)
                    console.print(f"[green]✓ Crawl successful[/green]")
                    console.print(Panel(f"URL: {data.get('url')}\nDoc ID: {data.get('doc_id')}", title="Crawl Result"))
                    return True
                else:
                    progress.update(task, completed=100)
                    console.print(f"[red]✗ Crawl failed: {data.get('message')}[/red]")
                    return False
            else:
                progress.update(task, completed=100)
                console.print(f"[red]✗ Crawl request failed with status {response.status_code}[/red]")
                return False
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Crawl request error: {str(e)}[/red]")
        return False

def test_ask_question(base_url):
    """Test asking a question and getting a response with sources."""
    console.print("\n[bold blue]Testing Question Answering[/bold blue]")
    
    question = "What are the building rules?"
    
    try:
        console.print(f"Question: [cyan]{question}[/cyan]")
        
        response = requests.post(f"{base_url}/api/ask", json={"question": question, "top_k": 5})
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            if data.get("success"):
                console.print("[green]✓ Question answered successfully[/green]")
                
                # Display the answer
                console.print(Panel(data.get("answer", "No answer provided"), title="Answer"))
                
                # Display source information
                if data.get("chunks"):
                    table = Table(title="Source Information")
                    table.add_column("Page", style="cyan")
                    table.add_column("Section", style="green")
                    table.add_column("Content Preview", style="yellow")
                    
                    for chunk in data.get("chunks"):
                        metadata = chunk.get("metadata", {})
                        page = metadata.get("page_title", "Unknown")
                        section = metadata.get("section_header", "Unknown")
                        content = chunk.get("text", "")
                        content_preview = content[:100] + "..." if len(content) > 100 else content
                        
                        table.add_row(page, section, content_preview)
                    
                    console.print(table)
                
                return data
            else:
                console.print(f"[red]✗ Question answering failed: {data.get('message')}[/red]")
                return None
        else:
            console.print(f"[red]✗ Question request failed with status {response.status_code}[/red]")
            return None
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Question request error: {str(e)}[/red]")
        return None

def test_feedback_logging(base_url, question_data):
    """Test the feedback logging functionality."""
    console.print("\n[bold blue]Testing Feedback Logging[/bold blue]")
    
    if not question_data:
        console.print("[yellow]! Skipping feedback test as question data is not available[/yellow]")
        return False
    
    try:
        feedback_data = {
            "question": question_data.get("question"),
            "response": question_data.get("answer", ""),
            "chunk_ids": [chunk.get("metadata", {}).get("chunk_id") for chunk in question_data.get("chunks", []) if chunk.get("metadata", {}).get("chunk_id")],
            "rating": 5,
            "comments": "This is a test feedback from the deployment test script.",
            "user_id": "test_user",
            "session_id": f"test_session_{int(time.time())}"
        }
        
        response = requests.post(f"{base_url}/api/feedback", json=feedback_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            if data.get("success"):
                console.print("[green]✓ Feedback logged successfully[/green]")
                return True
            else:
                console.print(f"[red]✗ Feedback logging failed: {data.get('message')}[/red]")
                return False
        else:
            console.print(f"[red]✗ Feedback request failed with status {response.status_code}[/red]")
            return False
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Feedback request error: {str(e)}[/red]")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test the deployment of MetPol AI")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend API URL")
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold green]MetPol AI Deployment Test[/bold green]\n\n"
        f"Backend URL: [cyan]{args.backend_url}[/cyan]",
        title="Test Configuration"
    ))
    
    # Test backend connectivity
    if not test_backend_connectivity(args.backend_url):
        console.print("[bold red]Backend connectivity test failed. Aborting further tests.[/bold red]")
        sys.exit(1)
    
    # Test API endpoints
    api_results = test_api_endpoints(args.backend_url)
    
    # Test crawl functionality
    crawl_success = test_crawl_functionality(args.backend_url)
    
    # Test asking a question
    question_data = test_ask_question(args.backend_url)
    
    # Test feedback logging
    if question_data:
        feedback_success = test_feedback_logging(args.backend_url, question_data)
    else:
        feedback_success = False
    
    # Summary
    console.print("\n[bold blue]Test Summary[/bold blue]")
    
    table = Table(title="Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="green")
    
    table.add_row("Backend Connectivity", "[green]✓ Passed[/green]")
    table.add_row("API Endpoints", f"[{'green' if all(r['success'] for r in api_results) else 'red'}]{'✓ All Passed' if all(r['success'] for r in api_results) else '✗ Some Failed'}[/{'green' if all(r['success'] for r in api_results) else 'red'}]")
    table.add_row("Crawl Functionality", f"[{'green' if crawl_success else 'red'}]{'✓ Passed' if crawl_success else '✗ Failed'}[/{'green' if crawl_success else 'red'}]")
    table.add_row("Question Answering", f"[{'green' if question_data else 'red'}]{'✓ Passed' if question_data else '✗ Failed'}[/{'green' if question_data else 'red'}]")
    table.add_row("Feedback Logging", f"[{'green' if feedback_success else 'red'}]{'✓ Passed' if feedback_success else '✗ Failed'}[/{'green' if feedback_success else 'red'}]")
    
    console.print(table)
    
    # Overall result
    all_passed = all([
        True,  # Backend connectivity (we already exited if this failed)
        all(r["success"] for r in api_results),
        crawl_success,
        question_data is not None,
        feedback_success
    ])
    
    if all_passed:
        console.print(Panel("[bold green]All tests passed! The deployment is working correctly.[/bold green]", title="Success"))
    else:
        console.print(Panel("[bold yellow]Some tests failed. Please check the results above for details.[/bold yellow]", title="Warning"))

if __name__ == "__main__":
    main()
