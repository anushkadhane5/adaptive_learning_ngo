import random

NOUNS = ["dog", "cat", "teacher", "school", "book"]
VERBS = ["run", "eat", "play", "read", "write"]
ADJECTIVES = ["big", "happy", "fast", "blue", "tall"]

def generate_english_question(grade):

    if grade <= 3:
        word = random.choice(NOUNS)
        question = f"'{word}' is a ____"
        answer = "Noun"

    elif grade <= 6:
        word = random.choice(VERBS)
        question = f"'{word}' is a ____"
        answer = "Verb"

    else:
        word = random.choice(ADJECTIVES)
        question = f"'{word}' is a ____"
        answer = "Adjective"

    options = ["Noun", "Verb", "Adjective", "Adverb"]
    random.shuffle(options)

    return {
        "q": question,
        "options": options,
        "answer": answer
    }
