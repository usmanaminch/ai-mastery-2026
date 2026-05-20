import json
import os
from datetime import datetime

TODO_FILE = "todos.json"

def load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, 'r') as f:
            return json.load(f)
    return {"urgent": [], "this_week": [], "someday": []}

def save_todos(todos):
    with open(TODO_FILE, 'w') as f:
        json.dump(todos, f, indent=2)

def add_todo(item, priority="this_week"):
    todos = load_todos()
    todos[priority].append({
        "item": item,
        "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "done": False
    })
    save_todos(todos)
    print(f"✅ Added to {priority}: {item}")

def show_todos():
    todos = load_todos()
    print("\n🔴 URGENT:")
    for t in todos["urgent"]:
        status = "✅" if t["done"] else "⬜"
        print(f"  {status} {t['item']}")
    
    print("\n📅 THIS WEEK:")
    for t in todos["this_week"]:
        status = "✅" if t["done"] else "⬜"
        print(f"  {status} {t['item']}")
    
    print("\n💭 SOMEDAY:")
    for t in todos["someday"]:
        status = "✅" if t["done"] else "⬜"
        print(f"  {status} {t['item']}")

def complete_todo(priority, index):
    todos = load_todos()
    todos[priority][index]["done"] = True
    save_todos(todos)
    print(f"✅ Marked complete")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        show_todos()
    elif sys.argv[1] == "add":
        priority = sys.argv[3] if len(sys.argv) > 3 else "this_week"
        add_todo(sys.argv[2], priority)
    elif sys.argv[1] == "done":
        complete_todo(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1] == "show":
        show_todos()