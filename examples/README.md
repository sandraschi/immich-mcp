# ImmichMCP Examples

This directory contains example scripts demonstrating how to use the ImmichMCP DXT package.

## Available Examples

### 1. DXT Package Usage Example

**File:** `dxt_usage_example.py`

This example demonstrates various ways to use the DXT package with the ImmichMCP server, including:

- Loading and accessing DXT configuration
- Retrieving random prompts from different categories
- Generating a photo management plan
- Creating AI enhancement workflows
- Generating search queries
- Creating photo organization guides

#### How to Run

```bash
# Navigate to the project root directory
cd /path/to/immichmcp

# Install required dependencies
pip install -e .

# Run the example script
python examples/dxt_usage_example.py
```

#### Example Output

```
=== ImmichMCP DXT Package Usage Example ===

Available prompt categories:
1. photo_management
2. ai_enhancement
3. search_queries
4. organization
5. sharing
6. backup_recovery
7. ai_insights

=== Sample Photo Management Plan ===

Task 1 (photo_management - Priority 5):
- Organize my vacation photos from last summer into albums by location and events.
- Estimated time: 45 minutes

Task 2 (ai_enhancement - Priority 4):
- Enhance the colors and lighting in my sunset photos.
- Estimated time: 20 minutes

...
```

## Creating Your Own Examples

To create your own examples, you can import and use the `DXTPackager` class from the `dxt.package` module:

```python
from dxt.package import DXTPackager

# Initialize the packager
packager = DXTPackager()

# Load the configuration
config = packager.load_config()

# Access prompts
prompts = config.get("prompts", {})

# Use the prompts in your application
for category, prompt_list in prompts.items():
    print(f"Category: {category}")
    for prompt in prompt_list[:3]:  # Show first 3 prompts
        print(f"- {prompt}")
    print()
```

## Contributing

If you've created an example that you think would be helpful to others, please consider submitting a pull request to include it in this directory.
