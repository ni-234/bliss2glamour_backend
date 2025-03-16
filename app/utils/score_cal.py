from ast import literal_eval

from ..database.models import Quiz
from ..database.schemas import SubmitQuizRequest


def calculate_quiz_score(quiz_result: SubmitQuizRequest, quiz: Quiz) -> int:
    try:
        quiz_data = literal_eval(quiz.quiz_json)
        correct_answers_data = literal_eval(quiz.quiz_answers)["quiz_answers"]
        submitted_answers = quiz_result.submitted_answers["answers"]
    except (SyntaxError, ValueError, KeyError) as e:
        print(f"Error parsing data: {e}")
        return 0

    question_map = {}
    for q in quiz_data.get("questions", []):
        question_map[int(q["question_id"])] = {
            "type": q["type"],
            "answers": q.get("answers", []),
            "correct": set(),
        }

    for correct in correct_answers_data:
        q_id = int(correct["question_id"])
        if q_id in question_map:
            question_map[q_id]["correct"] = set(correct["correct_answer"])

    total_score = 0
    for sub in submitted_answers:
        q_id = sub["question_id"]
        if q_id not in question_map:
            continue

        q_data = question_map[q_id]
        try:
            submitted_indices = [int(idx) - 1 for idx in sub["answer"]]
            submitted_answers = [q_data["answers"][i] for i in submitted_indices]
        except (IndexError, ValueError) as e:
            print(f"Invalid answer index for question {q_id}: {e}")
            continue

        if q_data["type"] == "single_choice":
            if (
                len(submitted_answers) == 1
                and submitted_answers[0] in q_data["correct"]
            ):
                total_score += 1
        elif q_data["type"] == "multiple_choice":
            if set(submitted_answers) == q_data["correct"]:
                total_score += 1

    total_questions = len(question_map)
    if total_questions == 0:
        return 0

    return round((total_score / total_questions) * 100)
