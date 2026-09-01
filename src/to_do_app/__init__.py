from datetime import datetime
from emoji import emojize
from rich import print as rprint
import argparse, re, json, os, sys

def configure_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", help="Item to add")
    parser.add_argument("--set-name", nargs=2, metavar=("ID", "NAME"), help="Change an existing task's name")
    
    parser.add_argument("--due", default="None", help="Due date")
    parser.add_argument("--set-date", nargs=2, metavar=("ID", "DATE"), help="Change an existing task's due date")
    
    parser.add_argument("--priority", default='medium', choices=["high", "medium", "low"], help="Priority when adding a task")
    parser.add_argument("--set-priority", nargs=2, metavar=("ID", "PRIORITY"), help="Change an existing task's priority")
    
    parser.add_argument("--category", default="None", help="Due date")
    parser.add_argument("--set-category", nargs=2, metavar=("ID", "CATEGORY"), help="Change an existing task's category")
    
    parser.add_argument("--filter", nargs='+', help="Filter by task status")
    
    parser.add_argument("--done", nargs="+", type=int, help="Mark a task as done")
    parser.add_argument("--undo", nargs="+", type=int, help="Mark a task as done")
    parser.add_argument("--delete", nargs="+", type=int, help="Delete a task")
    
    args = parser.parse_args()
    return args

def load_tasks() -> list[dict]:
    DEFAULT_TASK = {
        "completed": False,
        "due": None,
        "priority": "medium",
        "category": None,
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
    # check if no arguments at all
    if len(sys.argv) == 1:
        print("Welcome to the To-Do App! Use --help to see available commands.")
        return
        
    global FILE_NAME
    FILE_NAME = os.path.join(os.path.dirname(__file__), r"data\tasks.json")
    
    args = configure_cli()
    tasks = load_tasks()
    
    if args.add:
        add_task(tasks, args.add, args.due, args.priority, args.category)
    if args.set_name:
        change_name(tasks, *args.set_name)
    if args.set_date:
        change_date(tasks, *args.set_date)
    if args.set_priority:
        change_priority(tasks, args.set_priority)
    if args.set_category:
        change_category(tasks, args.set_category)
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
    if date_str == "None":
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

def add_task(tasks: list[dict], item: str, date, priority, category) -> None:
    if not is_valid_date(date):
            print("due date must be an appropriate date in DD/MM/YYYY format")
            return
    
    if date == "None":
        date = None
    if category == "None":
        category = "uncategorized"
    if category in ["all", "pending", "completed", "high", "low", "medium"]:
        category = "uncategorized"
        print("Category can't be any of these: all, pending, completed, high, low, medium; and was defaulted to uncategorized")
    
    new_id = max((task.get("id", 0) for task in tasks), default=0) + 1
    tasks.append({"id": new_id, 
                  "name": item,
                  "completed": False,
                  "due": date,
                  "priority": priority.lower(),
                  "category": category.capitalize(),
                  })
    save_tasks(tasks)
    print(f"Task {item} with id {new_id} was added successfully!")

def change_name(tasks, name_data):
    idx, name = name_data
    
    for task in tasks:
        if task['id'] == int(idx):
            task['name'] = name
    
    save_tasks(tasks)
    print(f"The task name of task_{idx} was successfully changed to {name}.")

def change_date(tasks, date_data):
    idx, date = date_data
    
    if not is_valid_date(date):
        print("due date must be an appropriate date in DD/MM/YYYY format")
        return
    
    for task in tasks:
        if task['id'] == int(idx):
            if date == "None":
                task['due'] = None
            else:
                task['due'] = date
    
    save_tasks(tasks)
    print(f"The due date of task_{idx} was successfully changed to {date}.")

def change_priority(tasks, priority_data):
    idx, priority = priority_data
    priority = priority.lower()
    
    if priority not in ["high", "medium", "low"]:
        raise ValueError("Priority must be on of the following: high, medium, or low!")
    
    for task in tasks:
        if task['id'] == int(idx):
            task['priority'] = priority
    
    save_tasks(tasks)
    print(f"The priority of task_{idx} was successfully changed to {priority}.")

def change_category(tasks, category_data):
    idx, category = category_data
    
    if category in ["all", "pending", "completed", "high", "low", "medium"]:
        category = "uncategorized"
        print("Category can't be any of these: all, pending, completed, high, low, medium; and was defaulted to None")
    
    category = category.capitalize()
    
    for task in tasks:
        if task['id'] == int(idx):
            if category == "None":
                task['category'] = "uncategorized"
            else:
                task['category'] = category
                
    save_tasks(tasks)
    print(f"The category of task_{idx} was successfully changed to {category}.")

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
    
    # make filters consistent
    filter_types = [filters.lower() for filters in filter_types]
    
    # first - load categories as list
    existing_categories = [t['category'] for t in tasks]

    # Cleanup
    possible_values = ["all", "pending", "completed", "high", "low", "medium", *list(map(str.lower, filter(lambda item: isinstance(item, str), existing_categories)))]
    check = 0
    for filters in filter_types:
        if filters in possible_values:
            check += 1
    if check == 0:
        return ["The filters specified were never found!"]
    
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
    
    
    
    # filter category
    
    
    # check for existing categories
    category_filter = [p for p in existing_categories if isinstance(p, str) and p.lower() in filter_types]
    if category_filter:
        return_values_copy = return_values.copy()
        return_values = []
    
        for return_tasks in return_values_copy:
            if return_tasks["category"] in category_filter:
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
        category_emotes = emojize(f":{values['category']}:")
        
        output.append(f"[blue]{category_emotes}[/blue] [{colors}]{values['name']} (due: {values['due']}), [italic]id={values['id']}[/italic][/{colors}]")
    
    return output

if __name__ == "__main__":
    main()