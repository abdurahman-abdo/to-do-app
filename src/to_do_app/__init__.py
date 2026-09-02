from datetime import date, datetime
from emoji import emojize
from typing import Iterator
from rich import print as rprint
import argparse, re, json, os, sys

def configure_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", metavar="NEW_TASK_NAME", help="Add a new task for the first time, declaring the task's name")
    parser.add_argument("--set-name", nargs=2, metavar=("TASK_ID", "TASK_NAME"), help="Change an existing task's name")
    
    parser.add_argument("--due", default="None", metavar="DD/MM/YYYY", help="Assign a task's due date for the first time (use directly after --add) [optional, omit for no due date]")
    parser.add_argument("--set-date", nargs=2, metavar=("TASK_ID", "NEW_DATE"), help="Change an existing task's due date")
    
    parser.add_argument("--priority", default='medium', choices=["high", "medium", "low"], help="Assign a task's priority level for the first time (use directly after --add) [optional, omit for medium priority]")
    parser.add_argument("--set-priority", nargs=2, metavar=("TASK_ID", "NEW_PRIORITY"), help="Change an existing task's priority level")
    
    parser.add_argument("--category", default="uncategorized", metavar="CATEGORY", help="Assign a task category for the first time (use directly after --add) [optional, omit for uncategorized]")
    parser.add_argument("--set-category", nargs=2, metavar=("TASK_ID", "NEW_CATEGORY"), help="Change an existing task's category")
    
    parser.add_argument("--filter", metavar="FILTER", nargs='+', help="Filter by status, priority, or category (e.g. pending, high, work)")
    
    parser.add_argument("--done", nargs="+", metavar="TASK_ID", type=int, help="Mark a task as done by passing in a task id")
    parser.add_argument("--undo", nargs="+", metavar="TASK_ID", type=int, help="Mark a task as not done (undo completion) by passing in a task id")
    parser.add_argument("--delete", nargs="+", metavar="TASK_ID", type=int, help="Delete a task by passing in a task id")
    
    args = parser.parse_args()
    return args

def load_tasks() -> list[dict]:
    DEFAULT_TASK = {
        "completed": False,
        "due": None,
        "priority": "medium",
        "category": "uncategorized",
    }
    
    if not os.path.exists(FILE_NAME):
        return []
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            raw_tasks = json.load(file)
    except (json.JSONDecodeError, IOError):
        return []
    
    
    tasks = [{**DEFAULT_TASK, **task} for task in raw_tasks]
    
    # first - cleanup and load categories
    for task in tasks:
        if task['category'] is None or task['category'] == "None":
            task['category'] = "uncategorized"
    
    return tasks

def save_tasks(tasks: list[dict]) -> None:
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

def add_task(tasks: list[dict], item: str, date: str, priority: str, category: str) -> None:
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
                  "category": category.title(),
                  })
    save_tasks(tasks)
    print(f"Task {item} with id {new_id} was added successfully!")

def change_name(tasks: list[dict], name_data: list[str]) -> None:
    idx, name = name_data
    
    for task in tasks:
        if task['id'] == int(idx):
            task['name'] = name
    
    save_tasks(tasks)
    print(f"The task name of task_{idx} was successfully changed to {name}.")

def change_date(tasks: list[dict], date_data: list[str]) -> None:
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

def change_priority(tasks: list[dict], priority_data: list[str]) -> None:
    idx, priority = priority_data
    priority = priority.lower()
    
    if priority not in ["high", "medium", "low"]:
        raise ValueError("Priority must be on of the following: high, medium, or low!")
    
    for task in tasks:
        if task['id'] == int(idx):
            task['priority'] = priority
    
    save_tasks(tasks)
    print(f"The priority of task_{idx} was successfully changed to {priority}.")

def change_category(tasks: list[dict], category_data: list[str]) -> None:
    idx, category = category_data
    
    if category in ["all", "pending", "completed", "high", "low", "medium"]:
        category = "uncategorized"
        print("Category can't be any of these: all, pending, completed, high, low, medium; and was defaulted to uncategorized!")
    
    category = category.title()
    
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

def filter_task_status(tasks : list[dict], status_filters: list) -> Iterator[dict]:
    completed_tasks = [task for task in tasks if task["completed"]]
    pending_tasks = [task for task in tasks if not task["completed"]]
    
    for task in tasks:
        # check filters
        if ("pending" in status_filters) or ("completed" in status_filters):
            if "pending" in status_filters:
                if not len(pending_tasks):
                    return
                if not task['completed']:
                    yield task
            if "completed" in status_filters:
                if not len(completed_tasks):
                    return
                if task['completed']:
                    yield task
        # if nothing is passed or if all
        else:
            yield task

def filter_task_priority(tasks: list[dict], priority_filter: list) -> Iterator[dict]:
    for task in tasks:
        if task["priority"] in priority_filter:
            yield task

def filter_task_category(tasks: list[dict], category_filter: list) -> Iterator[dict]:
    for task in tasks:
        if task["category"] in category_filter:
            yield task

def configure_date(task: dict) -> tuple[date, date]:
    today = datetime.now().date()
    try:
        due_date = datetime.strptime(task['due'], "%d/%m/%Y").date()
    except (TypeError, ValueError, KeyError):
        due_date = datetime.max.date()
    
    return today, due_date

def set_color(task: dict, today: date, due_date: date) -> str:
    if task['completed']:
            return "dim white"
    if today > due_date:
            return "bold red"
    
    match task['priority']:
        case "low":
            return "green"
        case "medium":
            return "yellow"
        case "high":
            return "bold magenta"
    
    return "white"

def generate_emoji(task: dict) -> str:
    emoji_map = {
    "work": "briefcase",
    "personal": "bust_in_silhouette",
    "shopping": "shopping_cart",
    "groceries": "shopping_bags",
    "health": "stethoscope",
    "fitness": "muscle",
    "finance": "money_with_wings",
    "bills": "receipt",
    "home": "house",
    "family": "family",
    "travel": "airplane",
    "study": "books",
    "school": "graduation_cap",
    "work_urgent": "rotating_light",
    "social": "speech_balloon",
    "food": "fork_and_knife",
    "car": "car",
    "pets": "paw_prints",
    "hobby": "art",
    "reading": "open_book",
    "coding": "computer",
    "meeting": "calendar",
    "birthday": "birthday",
    "gift": "gift",
    "cleaning": "broom",
    "garden": "seedling",
    "appointment": "date",
    "medicine": "pill",
    "urgent": "warning",
    "uncategorized": "file_folder",
}
    
    for key, shortcode in emoji_map.items():
        if key in task['category'].lower():
            return emojize(f":{shortcode}:")
    
    return emojize(":question:")

def filter_tasks(tasks: list[dict], filter_types: list[str]) -> list:
    if not tasks:
        return ["No tasks found!"]
    
    # make filters consistent
    filter_types = [filters.lower() for filters in filter_types]
    existing_categories = [t['category'] for t in tasks]

    # Cleanup
    possible_values = ["all", "pending", "completed", "high", "low", "medium", *list(map(str.lower, filter(lambda item: isinstance(item, str), existing_categories)))]
    if not any(filters in possible_values for filters in filter_types):
        return ["The filters specified were never found!"]
    
    # filter statuses
    if "pending" in filter_types and not any(not t['completed'] for t in tasks):
        return ["No pending tasks found!"]
    if "completed" in filter_types and not any(t['completed'] for t in tasks):
        return ["No completed tasks found!"]

    status_filter_values = filter_task_status(tasks, filter_types)
    return_values = list(status_filter_values)
    
    # filter priorities
    priority_filter = [p for p in ["high", "medium", "low"] if p in filter_types]
    if priority_filter:
        priority_filter_values = filter_task_priority(return_values, priority_filter)
        return_values = list(priority_filter_values)
    
    # filter categories
    category_filter = [p for p in existing_categories if isinstance(p, str) and p.lower() in filter_types]
    if category_filter:
        category_filter_values = filter_task_category(return_values, category_filter)
        return_values = list(category_filter_values)
    
    # final checkup and result
    if not return_values:
        return ["No tasks match the selected filters"]
    
    output = []
    for values in return_values:
        today, due_date = configure_date(values)
            
        color = set_color(values, today, due_date)
        
        category_emoji = generate_emoji(values)
        
        RETURN_TEMPLATE = f"[blue]{category_emoji}[/blue]  [{color}]{values['name']} (due: {values['due']}), [italic]id={values['id']}[/italic][/{color}]"
        
        output.append(RETURN_TEMPLATE)
    
    return output

if __name__ == "__main__":
    main()