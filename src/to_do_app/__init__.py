from datetime import date, datetime
from emoji import emojize
from typing import Iterator
from rich import print as rprint
import argparse, re, json, os, sys

FILE_NAME = os.path.join(os.path.dirname(__file__), "data", "tasks.json")
os.makedirs(os.path.dirname(FILE_NAME), exist_ok=True)

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
    
    parser.add_argument("--filter", metavar="FILTER_VALUE", nargs='+', help="Filter by status, priority, or category (e.g. pending, high, work)")
    parser.add_argument("--sort", metavar="VALUE", nargs='+', help="Sort by name and due date, default is ascending (e.g. name ascending, date descending) [use save at the end if you want that specific sort to be saved]")
    parser.add_argument("--show", metavar="TASK_ID", nargs='+', type=int, help="Show a specific task or multiple tasks based by passing in a task id/ids. [You can pass -1 to output all tasks]")
    
    parser.add_argument("--done", nargs="+", metavar="TASK_ID", type=int, help="Mark a task or multiple tasks as done by passing in a task id/ids [You can pass -1 to mark all tasks as done]")
    parser.add_argument("--reopen", nargs="+", metavar="TASK_ID", type=int, help="Mark a task or multiple tasks as pending (undo completion) by passing in a task id/ids [You can pass -1 to mark all tasks as not done]")
    parser.add_argument("--delete", nargs="+", metavar="TASK_ID", type=int, help="Delete a task or multiple tasks by passing in a task id/ids [You can pass -1 to delete all tasks]")
    
    return parser.parse_args()

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
        print("Warning: tasks file was corrupted, starting fresh.")
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
    
    args = configure_cli()
    tasks = load_tasks()
    
    if args.add:
        add_task(tasks, args.add, args.due, args.priority, args.category)
    if args.set_name:
        change_name(tasks, args.set_name)
    if args.set_date:
        change_date(tasks, args.set_date)
    if args.set_priority:
        change_priority(tasks, args.set_priority)
    if args.set_category:
        change_category(tasks, args.set_category)
    if args.done:
        complete_task(tasks, *args.done)
    if args.reopen:
        reopen_task(tasks, *args.reopen)
    if args.delete:
        delete_task(tasks, *args.delete)
    if args.show:
        for line in show_tasks(tasks, *args.show):
            rprint(line)
    if args.sort:
        for line in sort_tasks(tasks, args.sort):
            rprint(line)
    if args.filter:
        for line in filter_tasks(tasks, args.filter):
            rprint(line)
    
    # whatever the case, finally print a summary
    if tasks:
        print("---------------------------")
        print(generate_summary(tasks))

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

def add_task(tasks: list[dict], item: str, due_date: str, priority: str, category: str) -> None:
    if not is_valid_date(due_date):
            print("due date must be an appropriate date in DD/MM/YYYY format")
            return
    
    if due_date == "None":
        due_date = None
    if category.lower() in {"all", "pending", "completed", "high", "low", "medium", "none"}:
        category = "uncategorized"
        print("Category can't be none or any of these: all, pending, completed, high, low, medium; and was defaulted to uncategorized")
    
    new_id = max((task.get("id", 0) for task in tasks), default=0) + 1
    tasks.append({
        "id": new_id, 
        "name": item,
        "completed": False,
        "due": due_date,
        "priority": priority.lower(),
        "category": category.lower(),
    })
    save_tasks(tasks)
    print(f"Task {item} with id {new_id} was added successfully!")

def change_name(tasks: list[dict], name_data: list[str]) -> None:
    idx, name = name_data
    
    for task in tasks:
        if task['id'] == int(idx):
            task['name'] = name
            print(f"The task name of task_{idx} was successfully changed to {name}.")
            break
    else:
        print(f"No task found with id {idx}.")
        return

    save_tasks(tasks)

def change_date(tasks: list[dict], date_data: list[str]) -> None:
    idx, due_date = date_data
    
    if not is_valid_date(due_date):
        print("due date must be an appropriate date in DD/MM/YYYY format")
        return
    
    for task in tasks:
        if task['id'] == int(idx):
            task['due'] = None if due_date == "None" else due_date
            print(f"The due date of task_{idx} was successfully changed to {due_date}.")
            break
    else:
        print(f"No task found with id {idx}.")
        return

    save_tasks(tasks)

def change_priority(tasks: list[dict], priority_data: list[str]) -> None:
    idx, priority = priority_data
    priority = priority.lower()
    
    if priority not in {"high", "medium", "low"}:
        print("Priority must be one of the following: high, medium, or low!")
        return
    
    for task in tasks:
        if task['id'] == int(idx):
            task['priority'] = priority
            print(f"The priority of task_{idx} was successfully changed to {priority}.")
            break
    else:
        print(f"No task found with id {idx}.")
        return

    save_tasks(tasks)

def change_category(tasks: list[dict], category_data: list[str]) -> None:
    idx, category = category_data
    
    if category.lower() in {"all", "pending", "completed", "high", "low", "medium", "none"}:
        category = "uncategorized"
        print("Category can't be none or any of these: all, pending, completed, high, low, medium; and was defaulted to uncategorized!")

    category = category.lower()
    
    for task in tasks:
        if task['id'] == int(idx):
            task['category'] = category
            print(f"The category of task_{idx} was successfully changed to {category}.")
            break
    else:
        print(f"No task found with id {idx}.")
        return
    save_tasks(tasks)

def complete_task(tasks: list[dict], *ids: int) -> None:
    if not tasks:
        print("No tasks found!")
        return

    if -1 in ids:
        for task in tasks:
            task['completed'] = True
            print(f"Task: \"{task['name']}\" was successfully marked as complete!")
        save_tasks(tasks)
        return
    
    matched = False
    for task in tasks:
        if task['id'] in ids:
            task['completed'] = True
            print(f"Task: \"{task['name']}\" was successfully marked as complete!")
            matched = True
    
    if not matched:
        print("No task found with the given ids.")
        return

    save_tasks(tasks)

def reopen_task(tasks: list[dict], *ids: int) -> None:
    if not tasks:
        print("No tasks found!")
        return

    if -1 in ids:
        for task in tasks:
            task['completed'] = False
            print(f"Task: \"{task['name']}\" was successfully marked as pending!")
        save_tasks(tasks)
        return
    
    matched = False
    for task in tasks:
        if task['id'] in ids:
            task['completed'] = False
            print(f"Task: \"{task['name']}\" was successfully marked as pending!")
            matched = True
    
    if not matched:
        print("No task found with the given ids.")
        return

    save_tasks(tasks)

def delete_task(tasks: list[dict], *ids: int) -> None:
    if not tasks:
        print("No tasks found!")
        return

    if -1 in ids:
        temp_tasks = tasks.copy()
        for task in temp_tasks:
            task_name = task['name']
            tasks.remove(task)
            print(f"Task: \"{task_name}\" was successfully deleted!")
        save_tasks(tasks)
        return
    
    remaining = [task for task in tasks if task['id'] not in ids]
    removed = [task for task in tasks if task['id'] in ids]
    
    if not removed:
        print("No task found with the given ids.")
        return

    for task in removed:
        print(f"Task: \"{task['name']}\" was removed successfully!")
    tasks[:] = remaining
    save_tasks(remaining)

def show_tasks(tasks: list[dict], *ids: int):
    if not tasks:
        return ["No tasks found!"]
    if -1 in ids:
        return print_output(tasks)
    
    if return_values := [task for task in tasks if task['id'] in ids]:
        return print_output(return_values)
        
    return ["No tasks were found with the given id(s)!"]

def sort_tasks(tasks: list[dict], sorting_data: list[str]):
    if not tasks:
        print("No tasks found!")
        return

    cleaned_data = [s.lower() for s in sorting_data]
    
    # check if the user wants to save
    if save := 'save' in cleaned_data:
        cleaned_data.remove('save')
    
    # Validate sorting_data's count
    if not (1 <= len(cleaned_data) <= 2):
        print(
            "Sort usage was incorrect!\n"
            "Sort by name and due date, default is ascending (e.g. 'name ascending', 'date descending')\n"
            "[use 'save' at the end if you want that specific sort to be saved]"
        )
        return
    
    # Assign sorting configuration
    key = cleaned_data[0]
    direction = cleaned_data[1] if len(cleaned_data) == 2 else "ascending"

    # Validate directional parameter
    if direction not in ("ascending", "descending"):
        print(
            f"Invalid order '{direction}'. Use 'ascending' or 'descending'."
        )
        return
    ascending = direction == "ascending"
    
    # sort accordingly
    if 'date' in key or 'due' in key:
        tasks.sort(
            key=lambda x: (
                (
                    datetime.strptime(x['due'], "%d/%m/%Y") 
                    if x.get('due') 
                    else datetime.max
                    ), 
                x.get("name", "").lower()
            ),
            reverse=not ascending
        )
    elif 'name' in key:
        tasks.sort(
            key=lambda x: x.get("name", "").lower(), 
            reverse=not ascending
        )
    else:
        print(f"Unknown key \"{key}\". 'name' and 'date' are the only valid ones!")
        return
    
    # save and return sorted tasks
    if save:
        save_tasks(tasks)
    
    return print_output(tasks)

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
        # work / career
        r"work|job|career": "briefcase",
        "work_urgent": "rotating_light",
        r"meeting|meetings": "calendar",
        r"deadline|deadlines": "hourglass_flowing_sand",
        r"project|projects": "clipboard",
        r"email|emails": "email",
        r"interview|interviews": "necktie",

        # personal / social
        "personal": "bust_in_silhouette",
        r"family": "family",
        r"friend|friends": "handshake",
        r"social": "speech_balloon",
        r"date|dating": "heart",
        r"birthday|b-?day": "birthday",
        r"gift|gifts|present|presents": "gift",
        r"party|parties": "tada",
        r"wedding": "ring",

        # shopping / errands
        r"shopping": "shopping_cart",
        r"grocer(?:y|ies)": "shopping_bags",
        r"errand|errands": "walking",
        r"return|returns": "package",

        # health / fitness
        r"health": "stethoscope",
        r"fitness|workout|gym|exercise": "muscle",
        r"run|running|jog|jogging": "runner",
        r"yoga|meditation|mindfulness": "person_in_lotus_position",
        r"sleep|rest": "sleeping",
        r"medicine|medication|medics?": "pill",
        r"appointment|appointments": "date",
        r"dentist|dental": "tooth",
        r"therapy|therapist": "brain",
        r"diet|nutrition": "green_salad",

        # finance
        r"finance|financial": "money_with_wings",
        r"bills?": "receipt",
        r"budget|budgeting": "bar_chart",
        r"tax|taxes": "money_with_wings",
        r"invest|investing|investment": "chart_with_upwards_trend",
        r"savings?": "bank",
        r"loan|loans|debt": "credit_card",

        # home / chores
        r"home|house": "house",
        r"cleaning|clean": "broom",
        r"laundry": "shirt",
        r"cooking|cook": "cooking",
        r"garden(?:s|ing)?": "seedling",
        r"repair|repairs|maintenance|fix": "hammer_and_wrench",
        r"move|moving|relocation": "moving_truck",

        # food
        r"foods?": "fork_and_knife",
        r"restaurant|dining|eating out": "fork_and_knife_with_plate",
        r"coffee": "coffee",
        r"baking|bake": "bread",

        # transport
        r"cars?": "car",
        r"travel|trip|trips|vacation": "airplane",
        r"flight|flights": "airplane_departure",
        r"train|trains": "steam_locomotive",
        r"parking": "parking",
        r"gas|fuel": "fuelpump",

        # study / school
        r"study|studies|studying": "books",
        r"school": "graduation_cap",
        r"homework": "pencil",
        r"exam|exams|test|tests": "memo",
        r"read(?:ing)?": "open_book",
        r"course|courses|class|classes": "school",

        # tech / coding
        r"coding|code|programming|dev": "computer",
        r"bug|bugs|debug|debugging": "beetle",
        r"design|ux|ui": "art",
        r"backup|backups": "floppy_disk",

        # hobbies / leisure
        r"hobby|hobbies": "art",
        r"music": "musical_note",
        r"movie|movies|film|films": "clapper_board",
        r"game|games|gaming": "video_game",
        r"photo|photos|photography": "camera",
        r"writing|write": "writing_hand",

        # pets / misc
        r"pets?": "paw_prints",
        r"vet|veterinary": "dog",

        # urgency / catch-all
        r"urgent|asap|important": "warning",
        r"uncategorized|misc|other|general": "file_folder",
    }
    
    category_lower = task['category'].lower()
    
    if category_lower in emoji_map:
        return emojize(f":{emoji_map[category_lower]}:")
    
    for key, shortcode in emoji_map.items():
        if re.search(rf"\b(?:{key})\b", category_lower):
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
    if all(filters not in possible_values for filters in filter_types):
        return ["The filters specified were never found!"]
    
    # filter statuses
    if "pending" in filter_types and all(task['completed'] for task in tasks):
        return ["No pending tasks found!"]
    if "completed" in filter_types and all(not task['completed'] for task in tasks):
        return ["No completed tasks found!"]

    status_filter_values = filter_task_status(tasks, filter_types)
    return_values = list(status_filter_values)
    
    # filter priorities
    if priority_filter:= [priority for priority in {"high", "medium", "low"} if priority in filter_types]:
        priority_filter_values = filter_task_priority(return_values, priority_filter)
        return_values = list(priority_filter_values)
    
    # filter categories
    if category_filter:= [p for p in existing_categories if isinstance(p, str) and p.lower() in filter_types]:
        category_filter_values = filter_task_category(return_values, category_filter)
        return_values = list(category_filter_values)
    
    # final checkup and result
    if not return_values:
        return ["No tasks match the selected filters"]
    
    return print_output(return_values)

def print_output(tasks: list[dict]) -> list:
    output = []
    for task in tasks:
        today, due_date = configure_date(task)
            
        color = set_color(task, today, due_date)
        
        category_emoji = generate_emoji(task)
        
        RETURN_TEMPLATE = f"[blue]{category_emoji}[/blue]  [{color}]{task['name']} (due: {task['due']}), [italic]id={task['id']}[/italic][/{color}]"
        
        output.append(RETURN_TEMPLATE)
    
    return output

def generate_summary(tasks: list[dict]) -> str:
    pending_count = 0
    completed_count = 0
    overdue = 0

    for task in tasks:
        if task["completed"]:
            completed_count += 1
        else:
            today, due_date = configure_date(task)
            
            if today > due_date:
                overdue += 1
            else:
                pending_count += 1

    return f"Summary: {len(tasks)} total, {pending_count} pending, {overdue} overdue, {completed_count} done."

if __name__ == "__main__":
    main()