import time


def validate_student(data):
    required = ("roll_no", "name", "class_name")
    for key in required:
        if not isinstance(data.get(key), str) or not data[key].strip():
            return f"{key.replace('_', ' ').title()} is required."
    if len(data["roll_no"].strip()) > 30:
        return "Roll number must be 30 characters or fewer."
    if len(data["name"].strip()) > 100:
        return "Student name must be 100 characters or fewer."
    if len(data["class_name"].strip()) > 60:
        return "Class/semester must be 60 characters or fewer."
    if not isinstance(data.get("department", "CSE"), str):
        return "Department must be text."
    for i in range(1, 6):
        key = f"subject{i}"
        try:
            mark = float(data[key])
        except (KeyError, TypeError, ValueError):
            return f"Marks for Subject {i} must be a number."
        if not 0 <= mark <= 100:
            return f"Marks for Subject {i} must be between 0 and 100."
    return None


def sort_key(student):
    # Higher percentage first, then total, then roll number for deterministic ties.
    return (-student["percentage"], -student["total"], student["roll_no"])


def merge_sort(items):
    if len(items) <= 1:
        return items[:]
    mid = len(items) // 2
    left = merge_sort(items[:mid])
    right = merge_sort(items[mid:])
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if sort_key(left[i]) <= sort_key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort(items):
    if len(items) <= 1:
        return items[:]
    pivot = items[len(items) // 2]
    pivot_key = sort_key(pivot)
    lower, equal, higher = [], [], []
    for item in items:
        key = sort_key(item)
        if key < pivot_key:
            lower.append(item)
        elif key > pivot_key:
            higher.append(item)
        else:
            equal.append(item)
    return quick_sort(lower) + equal + quick_sort(higher)


def rank_students(students, algorithm="merge"):
    start = time.perf_counter()
    if algorithm == "merge":
        ordered = merge_sort(students)
    elif algorithm == "quick":
        ordered = quick_sort(students)
    else:
        ordered = sorted(students, key=sort_key)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
    ranked = []
    for position, student in enumerate(ordered, start=1):
        record = dict(student)
        record["rank"] = position
        ranked.append(record)
    return {"students": ranked, "elapsed_ms": elapsed_ms}
