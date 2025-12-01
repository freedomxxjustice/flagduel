from math import ceil
from random import sample, shuffle
from typing import List
from db.models.flag import Flag 

async def create_casual_questions(num_questions: int, category: str = None) -> List[dict]:
    if category == "cis":
        all_flags = await Flag.filter(category__in=["ru_regions", "ua_regions", "by_regions"])
    elif category and category != "frenzy":
        all_flags = await Flag.filter(category=category)
    else:
        all_flags = await Flag.all()

    list_length = int(num_questions)
    if len(all_flags) < list_length:
        all_flags = await Flag.all() 
    
    easy_flags = [f for f in all_flags if f.difficulty <= 0.33]
    medium_flags = [f for f in all_flags if 0.34 <= f.difficulty <= 0.66]
    hard_flags = [f for f in all_flags if f.difficulty > 0.66]

    num_easy = ceil(list_length * 0.33)
    num_medium = ceil(list_length * 0.33)
    num_hard = list_length - num_easy - num_medium

    def safe_sample(pool, count):
        if len(pool) >= count:
            return sample(pool, count)
        needed = count - len(pool)
        rest = [f for f in all_flags if f not in pool]
        if len(rest) < needed: return pool 
        return pool + sample(rest, needed)

    selected_flags = []
    selected_flags += safe_sample(easy_flags, num_easy)
    selected_flags += safe_sample(medium_flags, num_medium)
    selected_flags += safe_sample(hard_flags, num_hard)
    
    selected_flags = selected_flags[:list_length]
    shuffle(selected_flags)

    questions = []
    for flag in selected_flags:
        incorrect_pool = [f for f in all_flags if f.id != flag.id]
        count_options = min(len(incorrect_pool), 5) 
        
        incorrect_options = sample(incorrect_pool, count_options)
        options = [f.name for f in incorrect_options] + [flag.name]
        shuffle(options)

        questions.append({
            "flag_id": flag.id,
            "image": flag.image, 
            "options": options,
            "correct_answer": flag.name,
        })
        
    return questions