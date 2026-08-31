from datetime import datetime
from rich import print as rprint
import argparse, re, json, os

def configure_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", help="Item to add")
    parser.add_argument("--set-name", nargs=2, metavar=("ID", "NAME"), help="Change an existing task's name")
    parser.add_argument("--due", help="Due date")
    parser.add_argument("--set-date", nargs=2, metavar=("ID", "DATE"), help="Change an existing task's due date")
    parser.add_argument("--priority", choices=["high", "medium", "low"], help="Priority when adding a task")
    parser.add_argument("--set-priority", nargs=2, metavar=("ID", "PRIORITY"), help="Change an existing task's priority")
    parser.add_argument(
        "--filter", 
        choices=["all", "pending", "completed", "low", "medium", "high"], 
        nargs='+',
        help="Filter by task status"
    )
    
    parser.add_argument("--done", nargs="+", type=int, help="Mark a task as done")
    parser.add_argument("--undo", nargs="+", type=int, help="Mark a task as done")
    parser.add_argument("--delete", nargs="+", type=int, help="Delete a task")
    
    args = parser.parse_args()
    
    # Require --due and --priority only when --add is present
    if args.add is not None and (args.due is None or args.priority is None):
        parser.error("--due and --priority is required when --add is used.")
    
    # Check date authenticity
    if args.due and not is_valid_date(args.due):
        parser.error("due date must be an appropriate date in DD/MM/YYYY format")
        
    return args

def load_tasks() -> list[dict]:
    DEFAULT_TASK = {
        "completed": False,
        "due": None,
        "priority": "medium"
    }
    
    if not os.path.exists(FILE_NAME):
        return []
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            raw_tasks = json.load(file)
    except (json.JSONDecodeError, IOError):
        return []
    
    return [{**DEFAULT_TASK, **task} for task in raw_tasks]

def save_tasks(tasks) -> None:
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=4)

def main() -> None:
    global FILE_NAME
    FILE_NAME = r'C:\Users\abdur\OneDrive\Documents\myProjects\to-do-app\src\to_do_app\tasks.json'
    
    args = configure_cli()
    tasks = load_tasks()
    
    if args.add:
        add_task(tasks, args.add, args.due, args.priority)
    if args.set_name:
        change_name(tasks, *args.set_name)
    if args.set_date:
        change_date(tasks, *args.set_date)
    if args.set_priority:
        change_priority(tasks, args.set_priority)
    if args.done:
        complete_task(tasks, *args.done)
    if args.undo:
        undo_task(tasks, *args.undo)
    if args.delete:
        delete_task(tasks, *args.delete)
    if args.filter:
        for line in filter_tasks(tasks, args.filter):
            rprint(line)
    
def is_valid_date(date_str: str) -> bool:
    if date_str is None:
        return True
    
    # Check format DD/MM/YYYY for years 2000+
    if not re.match(r"^\d{2}/\d{2}/2\d{3}$", date_str):
        return False
    
    try:
        # Validates actual calendar logic (31st limits, leap years, etc.)
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def add_task(tasks: list[dict], item: str, date: str, priority: str) -> None:
    tasks.append({"id": max((task.get("id", 0) for task in tasks), default=0) + 1, 
                  "name": item,
                  "completed": False,
                  "due": date,
                  "priority": priority.lower()})
    print("Task added successfully")
    save_tasks(tasks)

def change_priority(tasks, priority_data):
    idx, priority = priority_data
    
    if priority not in ["high", "medium", "low"]:
        raise ValueError("Priority must be on of the following: high, medium, or low!")
    
    for task in tasks:
        if task['id'] == int(idx):
            task['priority'] = priority
    save_tasks(tasks)

def change_date(tasks, date_data):
    idx, date = date_data
    
    if not is_valid_date(date):
        print("due date must be an appropriate date in DD/MM/YYYY format")
        return
    
    for task in tasks:
        if task['id'] == int(idx):
            task['due'] = date
    save_tasks(tasks)

def complete_task(tasks: list[dict], *ids: int) -> None:
    for task in tasks:
        if task['id'] in ids:
            task['completed'] = True
            print(f"Task: \"{task['name']}\" was successfully marked as complete!")
    save_tasks(tasks)
    
def undo_task(tasks: list[dict], *ids: int) -> None:
    for task in tasks:
        if task['id'] in ids:
            task['completed'] = False
            print(f"Task: \"{task['name']}\" was successfully undone!")
    save_tasks(tasks)

def delete_task(tasks: list[dict], *ids: int) -> None:
    remaining = [task for task in tasks if task['id'] not in ids]
    removed = [task for task in tasks if task['id'] in ids]
    for task in removed:
        print(f"Task: \"{task['name']}\" was removed successfully!")
    save_tasks(remaining)

def filter_tasks(tasks: list[dict], filter_types: list) -> None:
    if not tasks:
        return ["No tasks found!"]
    return_values = []
    
    
    
    # filter status
    today = datetime.now().date()
    completed_tasks = [task for task in tasks if task["completed"]]
    pending_tasks = [task for task in tasks if not task["completed"]]
    
    for task in tasks:
        # check filters
        if ("pending" in filter_types) or ("completed" in filter_types):
            if "pending" in filter_types:
                if not len(pending_tasks):
                    return ["No pending tasks found!"]
                if not task['completed']:
                    return_values.append(task)
            if "completed" in filter_types:
                if not len(completed_tasks):
                    return ["No completed tasks found!"]
                if task['completed']:
                    return_values.append(task)
        # if nothing is passed or if all
        else:
            return_values.append(task)
    
    
    
    # filter priority
    priority_filter = [p for p in ["high", "medium", "low"] if p in filter_types]
    if priority_filter:
        return_values_copy = return_values.copy()
        return_values = []
    
        for return_tasks in return_values_copy:
            if return_tasks["priority"] in priority_filter:
                return_values.append(return_tasks)
    
    
    
    # final result
    output = []
    if not return_values:
        return ["No tasks match the selected filters"]
    
    for values in return_values:
        try:
            due_date = datetime.strptime(values['due'], "%d/%m/%Y").date()
        except TypeError:
            due_date = datetime.max.date()
        
        colors = 'dim white' if values['completed'] else 'bold red' if today > due_date else 'green' if values['priority'] == "low" else 'yellow' if values['priority'] == "medium" else 'bold magenta' if values['priority'] == "high" else 'white'
        
        output.append(f"[{colors}] {values['name']} (due: {values['due']}), [italic]id={values['id']}[/italic][/{colors}]")
        
    return output

if __name__ == "__main__":
    main()