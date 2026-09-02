## 📝 CLI To-Do App
A command-line task manager built with Python, featuring priorities, categories, due dates, and colorized filtering. Every task gets an emoji-tagged category and a due-date-aware color status, so a quick `--filter <option>` gives you an instant read on what's overdue, what's urgent, and what can wait.

## ✨ Technologies
- `Python`
- `argparse`
- `rich`
- `emoji`
- `uv`

## 🚀 Features
- Add, edit, complete, undo, and delete tasks by ID
- Priority levels (high/medium/low) with color-coded output
- Custom categories with emoji icons, falling back to default for unmapped ones
- Multi-value filtering; can combine status, priority, and category in one command
- Automatically flags overdue tasks in red, regardless of priority
- Persists everything to a local JSON file, with safe defaults for missing/malformed data

## 📍 The Process
I wanted to actually learn argparse and JSON persistence properly, not just build another todo-list tutorial clone. Started with the basics — add, list, delete — then kept running into real edge cases: what happens when two tasks share a name? What if the JSON file has old data missing new fields? What if someone tries to filter by a category that doesn't exist? Each of those pushed the design further. Task IDs instead of name-matching, default-filling on load, a pre-check that rejects filters matching nothing, and the like. Priorities and categories came next, which meant untangling an argument that was secretly doing two different jobs (`--priority` for adding vs. changing), and eventually splitting filtering into separate status/priority/category generator functions instead of one sprawling `elif` chain.  
Along the way I also used this as a chance to actually practice git properly by small commits, one feature at a time, instead of one giant dump at the end. It's not like a UI project, but it's a solid project to get comfortable with real Python patterns.

## 🚦 Running the Project
1. Clone the repository
```bash
   git clone https://github.com/abdurahman-abdo/to-do-app.git
   cd to-do-app
```
2. Install dependencies (uv creates the virtual environment automatically)
```bash
   uv sync
```
3. Run the app
```bash
   uv run todo --help
```
### Usage Options:

#### Creating & Editing
--add, --set-name, --due, --set-date, --priority, --set-priority, --category, --set-category

#### Viewing
--filter

#### Status & Deletion
--done, --undo, --delete

#### Examples
```bash
uv run todo --add "Buy groceries" --due 05/09/2026 --priority high --category groceries
uv run todo --filter pending high
uv run todo --set-priority 3 low
uv run todo --done 1 4 7
```

#### Full Reference:
  `-h`/`--help`           
            shows help message
  `--add` **[NEW_TASK_NAME]**   
                        Add a new task for the first time, declaring the task's name
  `--set-name` **[TASK_ID TASK_NAME]**
                        Change an existing task's name
  `--due` **[DD/MM/YYYY]**      
                        Assign a task's due date for the first time (use directly after --add) [optional, omit for no due date]
  `--set-date` **[TASK_ID NEW_DATE]**
                        Change an existing task's due date
  `--priority` **[{high,medium,low}]**
                        Assign a task's priority level for the first time (use directly after --add) [optional, omit for medium priority]
  `--set-priority` **[TASK_ID NEW_PRIORITY]**
                        Change an existing task's priority level
  `--category` **[CATEGORY]**   
                        Assign a task category for the first time (use directly after --add) [optional, omit for uncategorized]
  `--set-category` **[TASK_ID NEW_CATEGORY]**
                        Change an existing task's category
  `--filter` **[FILTER ...]**
                        Filter by status, priority, or category (e.g. pending, high, work) [can choose multiple filters]
  `--done` **[TASK_ID ...]**
                        Mark task/s as done by passing in a task id
  `--undo` **[TASK_ID ...]**
                        Mark task/s as not done (undo completion) by passing in a task id
  `--delete` **[TASK_ID ...]**
                        Delete task/s by passing in a task id
