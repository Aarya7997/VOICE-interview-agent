"""Single source of truth for the reference Q&A.

ALL question-set access goes through here, so the rest of the codebase never
touches files or formats directly. Adding/editing a question — whether by
hand-editing the YAML or via the in-app editor — needs ZERO changes to the
interview logic. Dropping a brand-new YAML into questions/ makes it appear in
the app automatically (auto-discovery), again with no code change.
"""

import glob
import os
import yaml

QUESTIONS_DIR = "questions"
REQUIRED = ("question", "ideal_answer", "key_points")


class QAValidationError(ValueError):
    """Raised when a question set is malformed — surfaced to the user clearly."""


def path_for(name: str) -> str:
    return os.path.join(QUESTIONS_DIR, f"{name}.yaml")


def list_sets() -> list[str]:
    """Every *.yaml in questions/ becomes a selectable set automatically."""
    files = sorted(glob.glob(os.path.join(QUESTIONS_DIR, "*.yaml")))
    return [os.path.splitext(os.path.basename(f))[0] for f in files]


def mtime(name: str) -> float:
    """Used to bust the cache so edits show up without a restart."""
    return os.path.getmtime(path_for(name))


def load(name: str) -> dict:
    with open(path_for(name), encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _validate(data)
    return data


def save(name: str, data: dict) -> None:
    _validate(data)
    with open(path_for(name), "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _validate(data: dict) -> None:
    if not data.get("role"):
        raise QAValidationError("The set needs a 'role' field.")
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise QAValidationError("The set needs a non-empty 'questions' list.")
    for i, q in enumerate(questions, 1):
        for field in REQUIRED:
            if not q.get(field):
                raise QAValidationError(f"Question #{i} is missing '{field}'.")
        if not isinstance(q["key_points"], list) or not q["key_points"]:
            raise QAValidationError(
                f"Question #{i}: 'key_points' must be a non-empty list.")
