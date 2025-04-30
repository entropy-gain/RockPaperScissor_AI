# 🪨📄✂️ Rock-Paper-Scissors Online Learning Agent

A lightweight **reinforcement learning system** that learns to beat humans in Rock-Paper-Scissors, deployed on Hugging Face Space with real-time strategy updates, caching, and experiment tracking.

---

## 🚀 Project Overview

This project is built for learning **ZenML**, reinforcement learning, and MLOps integration under resource-constrained environments like **Hugging Face Spaces**.

- 🔁 Online learning with game-by-game updates
- 💡 Dynamic strategy engine (Markov / Pattern / RL)
- 🧠 In-memory cache to reduce write load
- 🗃️ Periodic batch storage to SQLite
- 📊 Optional: ZenML pipeline to track policy updates & reward trends

---

## 🧩 Architecture Components

| Module              | Description |
|---------------------|-------------|
| **User Input**      | Rock, Paper, or Scissors |
| **Game Cache**      | Stores recent game logs and state in memory |
| **Strategy Engine** | Predicts next move using Markov or RL |
| **Evaluator**       | Computes result and reward |
| **Flush Manager**   | Writes cache to DB when triggered |
| **SQLite DB**       | Stores game history and strategy logs |
| **ZenML Pipeline**  | Tracks policy changes, metrics, artifacts |

---

## 🧠 Caching & Logging Strategy

- 🧠 `game_cache`: A fixed-size memory queue (`collections.deque`)
- 🔄 After N games or timeout, flush logs to `SQLite`
- 💾 `strategy_log.json`: Stores serialized strategy versions with timestamps
- 🔐 If cache is lost (e.g. on restart), reinitialize game and strategy

---

## 🗃️ Database Schema (SQLite)

### Table: `game_logs`

| Column | Type    | Description           |
|--------|---------|-----------------------|
| id     | INTEGER | Auto-increment key    |
| timestamp | TEXT | Game time (UTC)       |
| user_move | TEXT | Player move           |
| ai_move   | TEXT | AI predicted move     |
| result    | TEXT | `win`, `lose`, `draw` |
| reward    | REAL | Numeric reward        |
| strategy_version | TEXT | Strategy hash or version |

### Table: `policy_logs`

| Column | Type    | Description               |
|--------|---------|---------------------------|
| id     | INTEGER | Auto-increment key        |
| timestamp | TEXT | Time of update            |
| strategy_json | TEXT | Serialized strategy    |
| avg_reward | REAL | Average reward so far    |
| games_played | INTEGER | Total games since last update |

---

### Project Structure

```plaintext
RockPaperScissor/
├── RockPaperScissor/              # Main application package
│   ├── app.py                     # Application entry point and FastAPI setup
│   ├── config/                    # Configuration management
│   │   └── database.py           # Database configuration settings
│   │
│   ├── game_cache/               # In-memory caching module
│   │   ├── memory_cache.py       # Game session and LLM cache implementations
│   │   └── llm_cache.py          # LLM interaction caching
│   │
│   ├── models/                   # AI model implementations
│   │   └── ai_models.py          # Different AI strategies (Markov, Pattern, etc.)
│   │
│   ├── repositories/             # Data access and persistence logic
│   │   ├── storage.py           # Abstract storage interface
│   │   ├── sql_storage.py       # SQLite storage implementation
│   │   ├── s3_storage.py        # S3 storage implementation
│   │   └── combined_storage.py  # Combined S3 and SQL storage implementation
│   │
│   ├── routes/                   # API routing layer
│   │   └── game.py              # Game endpoints and request handling
│   │
│   ├── schemas/                  # Data validation and serialization
│   │   └── game.py              # Pydantic models for request/response
│   │
│   ├── services/                 # Business logic layer
│   │   ├── game_service.py      # Game logic and state management
│   │   └── llm_service.py       # LLM interaction handling
│   │
│   └── utils/                    # Utility functions
│       └── logging.py           # Logging configuration
│
├── data/                         # Data storage directory
│   └── game_data.db             # SQLite database file
│
├── frontend/                     # Frontend project
│   ├── index.html               # Main HTML entry page
│   └── webpage.html             # Secondary HTML page
│
├── logs/                        # Application logs
│   ├── app.log                 # General application logs
│   └── error.log               # Error logs
│
├── pyproject.toml               # Poetry dependency management
├── poetry.lock                  # Dependency lock file
├── .env                        # Environment variables
├── .gitignore                  # Git ignore file
└── README.md                   # Documentation
```

### Git Workflow and Best Practices

#### Branch Naming Convention

- **feature/xxx** - New features or enhancements
- **bugfix/xxx** - Bug fixes
- **hotfix/xxx** - Critical hotfixes for production
- **refactor/xxx** - Code refactoring without changing functionality
- **docs/xxx** - Documentation updates

#### Git Workflow

1. **Always create a new branch** for new work instead of pushing directly to `main`.
2. **Never push directly to `main`**; all code must go through a **merge request (pull request)**.
3. **Merge requests should be reviewed** before merging into `main`.
4. **Keep commits atomic**, meaning each commit should serve a single purpose.
5. **Write meaningful commit messages**, following the format: `type(scope): description` (e.g., `feat(game): add new AI model`).
6. **Sync with `main` regularly** to avoid merge conflicts.

#### Common Git Commands

```sh
# Check the current remote repository
git remote -v

# Check the current status of your repository
git status

# Add files to staging area
git add <file> # Add a specific file
git add .      # Add all changes

# Create a new branch
git branch feature/new-feature

# Switch to a branch
git checkout feature/new-feature

# Commit changes with a message
git commit -m "feat(game): improve AI prediction accuracy"

# Push changes to a remote branch
git push origin feature/new-feature

# Pull the latest changes from `main`
git pull origin main

# Merge another branch into your current branch
git merge feature/new-feature

# Delete a branch after merging
git branch -d feature/new-feature
```

#### Additional Git Tips for Beginners

- **Use descriptive branch names** that indicate their purpose.
- **Commit frequently** to avoid losing work.
- **Avoid large, unstructured commits**—each commit should ideally address a single issue.
- **Use `git stash`** to temporarily store changes when switching branches.
- **Review changes before committing** using `git diff`.
- **Always fetch the latest updates** using `git fetch` before working on a branch.
- **Resolve merge conflicts carefully** and test thoroughly after merging.

By following these best practices, we ensure a clean and maintainable codebase for the project.
