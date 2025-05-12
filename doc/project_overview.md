# Prompt Manager - Project Overview

The Prompt Manager is a standalone tool extracted from the Coordinator project, designed to efficiently manage, organize, and process text prompts. It provides a robust system for handling templates with inclusions and supports a RESTful API and WebSocket interface for real-time editing.

## Key Features

### Prompt Management

- Fragment and template management with support for markdown files
- Prompt composition through inclusions with syntax `[[prompt_id]]`
- Metadata handling with YAML front matter
- Circular dependency detection and prevention

### API Endpoints

- RESTful API for CRUD operations on prompt fragments and templates
- Support for rendering templates with inclusions expanded
- WebSocket interface for real-time editing

## Project Structure

```
prompt_manager/
├── bin/                # Helper scripts
├── config/             # Configuration files
├── doc/                # Documentation
│   └── progress/       # Progress updates
├── src/                # Source code
│   └── prompts/        # Prompt management system
│       ├── api/        # Prompt API
│       ├── models/     # Prompt data models
│       ├── services/   # Prompt services
│       ├── static/     # Static assets
│       └── templates/  # HTML templates
└── tests/              # Test cases
```

## Core Components

### Unified Prompt Model

The system uses a unified `Prompt` model that replaces the separate fragment and template models. This provides a more consistent interface and simplifies the codebase.

### Prompt Service

The `PromptService` class provides the core functionality:

- Loading and saving prompts to/from the filesystem
- Managing prompt directories
- Expanding inclusions in templates
- Detecting circular dependencies
- Finding prompts by ID, content, or metadata

### Inclusion Processing

Prompts can include other prompts using the `[[prompt_id]]` syntax. The system:

1. Detects inclusions in content
2. Resolves each inclusion to its corresponding prompt
3. Recursively expands nested inclusions
4. Detects and prevents circular dependencies
5. Returns the fully expanded content

## Recent Changes

The project has undergone several key improvements:
- Removal of the promptType functionality
- Improved handling of recursion and circular dependencies
- Enhanced test coverage for composite prompt handling

For detailed progress updates, see the documents in the `doc/progress/` directory.
