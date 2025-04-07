# Development Container for RockPaperScissor

This directory contains configuration files for setting up a consistent development environment using VS Code's Remote Containers feature.

## What's Included

- Python 3.10 environment
- Poetry for dependency management
- Local DynamoDB instance
- AWS CLI configured for local development
- Development tools: Black, isort, pylint, pytest, etc.

## Getting Started

1. Install [Docker](https://www.docker.com/products/docker-desktop)
2. Install [VS Code](https://code.visualstudio.com/)
3. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
4. Open this project in VS Code
5. When prompted to "Reopen in Container", click "Reopen in Container"
   - Alternatively, press F1, then select "Remote-Containers: Reopen in Container"

## Environment Variables

The development container sets the following environment variables:

- `AWS_ENV=local` - Indicates development environment
- `DB_MODE=local-dynamodb` - Uses local DynamoDB instance
- `LOG_LEVEL=INFO` - Sets logging level

## Initial Setup

When the container starts for the first time, Poetry will automatically install project dependencies defined in `pyproject.toml`.

## DynamoDB Local

The local DynamoDB instance is accessible:

- Inside the container at: `http://dynamodb-local:8000`
- From the host at: `http://localhost:8000`

You can run the included setup script to create required tables:

```bash
cd .devcontainer
chmod +x dynamodb-setup.sh
./dynamodb-setup.sh
```

## Running the Application

From within the container terminal:

```bash
# Run the application
python -m RockPaperScissor.app

# Run tests
pytest
```

The FastAPI application will be available at <http://localhost:8000>
