"""
DXT Package Usage Example for ImmichMCP

This script demonstrates how to use the DXT package with the ImmichMCP server.
It shows various ways to interact with the package, including loading configuration,
accessing prompts, and using them to enhance photo management tasks.
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import the DXTPackager class from the dxt package
from dxt.package import DXTPackager

class DXTUsageExample:
    """Example class demonstrating DXT package usage with ImmichMCP."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the example with a DXT config file."""
        self.packager = DXTPackager(config_path)
        self.config = self.packager.load_config()
        self.prompts = self.config.get("prompts", {})
        
    def get_random_prompt(self, category: str) -> str:
        """Get a random prompt from the specified category."""
        if category not in self.prompts or not self.prompts[category]:
            return f"No prompts found in category: {category}"
        return random.choice(self.prompts[category])
    
    def list_all_categories(self) -> List[str]:
        """List all available prompt categories."""
        return list(self.prompts.keys())
    
    def get_prompts_by_category(self, category: str) -> List[str]:
        """Get all prompts from a specific category."""
        return self.prompts.get(category, [])
    
    def generate_photo_management_plan(self) -> Dict[str, Any]:
        """Generate a photo management plan using prompts."""
        plan = {
            "generated_at": datetime.utcnow().isoformat(),
            "tasks": []
        }
        
        # Add a random task from each category
        for category in self.prompts:
            if category == "photo_management":
                # Add multiple photo management tasks since it's the main category
                for _ in range(3):
                    prompt = self.get_random_prompt(category)
                    plan["tasks"].append({
                        "category": category,
                        "prompt": prompt,
                        "priority": random.randint(1, 5),
                        "estimated_time": f"{random.randint(5, 60)} minutes"
                    })
            else:
                prompt = self.get_random_prompt(category)
                plan["tasks"].append({
                    "category": category,
                    "prompt": prompt,
                    "priority": random.randint(1, 5),
                    "estimated_time": f"{random.randint(5, 30)} minutes"
                })
        
        # Sort tasks by priority (highest first)
        plan["tasks"].sort(key=lambda x: x["priority"], reverse=True)
        return plan
    
    def create_ai_enhancement_workflow(self) -> Dict[str, Any]:
        """Create an AI enhancement workflow using prompts."""
        workflow = {
            "workflow_name": "AI_Enhancement_Pipeline",
            "created_at": datetime.utcnow().isoformat(),
            "steps": []
        }
        
        # Get AI enhancement prompts
        enhancement_prompts = self.get_prompts_by_category("ai_enhancement")
        
        # Create a workflow with up to 5 random enhancement steps
        for i, prompt in enumerate(random.sample(enhancement_prompts, min(5, len(enhancement_prompts))), 1):
            workflow["steps"].append({
                "step_id": i,
                "action": "ai_enhance",
                "prompt": prompt,
                "parameters": {
                    "strength": random.uniform(0.5, 1.0),
                    "model": random.choice(["style-transfer", "super-resolution", "color-enhancement", "object-removal"])
                }
            })
            
        return workflow
    
    def generate_search_queries(self, theme: str) -> List[Dict[str, str]]:
        """Generate search queries based on a theme."""
        search_queries = self.get_prompts_by_category("search_queries")
        
        # Filter queries that match the theme
        theme_queries = [q for q in search_queries if theme.lower() in q.lower()]
        
        if not theme_queries:
            # If no theme matches, return generic search queries
            theme_queries = random.sample(search_queries, min(5, len(search_queries)))
        
        return [{"query": q, "type": "search"} for q in theme_queries]
    
    def create_photo_organization_guide(self) -> Dict[str, Any]:
        """Create a guide for photo organization using prompts."""
        guide = {
            "title": "Photo Organization Guide",
            "created_at": datetime.utcnow().isoformat(),
            "sections": []
        }
        
        # Add an introduction
        guide["sections"].append({
            "title": "Introduction",
            "content": "This guide provides a structured approach to organizing your photo library using the DXT package for ImmichMCP."
        })
        
        # Add organization methods
        organization_methods = self.get_prompts_by_category("organization")
        for i, method in enumerate(organization_methods[:5], 1):  # Limit to 5 methods
            guide["sections"].append({
                "title": f"Method {i}",
                "description": method,
                "steps": [
                    "Select the photos you want to organize.",
                    f"Apply the following organization method: {method}",
                    "Review the results and make any necessary adjustments.",
                    "Save the organized collection."
                ]
            })
            
        # Add a conclusion
        guide["sections"].append({
            "title": "Conclusion",
            "content": "By following these methods, you can maintain a well-organized photo library that's easy to navigate and enjoy."
        })
        
        return guide


def main():
    """Run the DXT usage example."""
    print("=== ImmichMCP DXT Package Usage Example ===\n")
    
    # Initialize the example
    example = DXTUsageExample()
    
    # Display available categories
    print("Available prompt categories:")
    for i, category in enumerate(example.list_all_categories(), 1):
        print(f"{i}. {category}")
    
    # Generate and display a photo management plan
    print("\n=== Sample Photo Management Plan ===")
    plan = example.generate_photo_management_plan()
    for i, task in enumerate(plan["tasks"][:5], 1):  # Show first 5 tasks
        print(f"\nTask {i} ({task['category']} - Priority {task['priority']}):")
        print(f"- {task['prompt']}")
        print(f"- Estimated time: {task['estimated_time']}")
    
    # Show an AI enhancement workflow
    print("\n=== Sample AI Enhancement Workflow ===")
    workflow = example.create_ai_enhancement_workflow()
    print(f"Workflow: {workflow['workflow_name']}")
    for step in workflow["steps"]:
        print(f"\nStep {step['step_id']}:")
        print(f"- Action: {step['action']}")
        print(f"- Prompt: {step['prompt']}")
        print(f"- Parameters: {', '.join(f'{k}={v}' for k, v in step['parameters'].items())}")
    
    # Generate search queries for a theme
    theme = "portrait"
    print(f"\n=== Sample Search Queries for '{theme}' ===")
    queries = example.generate_search_queries(theme)
    for i, query in enumerate(queries[:3], 1):  # Show first 3 queries
        print(f"{i}. {query['query']}")
    
    # Generate a photo organization guide
    print("\n=== Photo Organization Guide Preview ===")
    guide = example.create_photo_organization_guide()
    print(f"Title: {guide['title']}")
    print(f"Sections: {len(guide['sections'])}")
    for section in guide['sections'][:3]:  # Show first 3 sections
        print(f"\n{section['title']}:")
        if 'description' in section:
            print(f"- {section['description']}")
        if 'steps' in section:
            for step in section['steps'][:2]:  # Show first 2 steps
                print(f"  - {step}")
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
