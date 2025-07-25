# ImmichMCP DXT Package

This directory contains the Data eXchange Template (DXT) packaging for the ImmichMCP project. The DXT package includes creative prompts and configuration templates for the Immich photo management system.

## What is DXT?

DXT (Data eXchange Template) is a packaging format that includes:

- **Creative Prompts**: Predefined natural language queries for the ImmichMCP system
- **Configuration Templates**: Predefined settings for different use cases
- **Metadata**: Information about the package, its author, and version

## Package Contents

- `dxt.json`: Main configuration file with creative prompts and package metadata
- `package.py`: Script to create DXT packages
- `README.md`: This file

## Creative Prompts

The DXT package includes creative prompts in several categories:

1. **Photo Management**: Commands for organizing and managing photos
2. **AI Enhancement**: Commands for enhancing and editing photos using AI
3. **Search Queries**: Example search queries for finding specific photos
4. **Organization**: Commands for organizing photos into albums and folders
5. **Sharing**: Commands for sharing photos with others

## Using the DXT Package

### Prerequisites

- Python 3.11+
- ImmichMCP server running

### Creating a DXT Package

1. Update the `dxt.json` file with your prompts and configuration
2. Run the packaging script:

```bash
python dxt/package.py
```

This will create a `.zip` file in the `dist` directory.

### Installing a DXT Package

1. Copy the `.zip` file to your ImmichMCP instance
2. Extract it to the appropriate directory
3. The prompts will be available in the ImmichMCP interface

## Customizing Prompts

Edit the `dxt.json` file to add or modify prompts. The file includes several categories of prompts that you can customize for your needs.

## License

This DXT package is licensed under the MIT License. See the main project LICENSE file for details.
