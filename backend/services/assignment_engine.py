"""
Assignment Engine Service
Intelligently assigns tasks to developers based on:
- Current workload (open task count)
- Skills / role match
- Availability
- Past performance (velocity)
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ─── Developer profile shape (mirrors models/developer.py) ───────────────────
# {
#   "id": int,
#   "name": str,
#   "role": "backend" | "frontend" | "fullstack" | "devops",
#   "skills": ["python", "fastapi", ...],
#   "open_tasks": int,
#   "velocity": float,          # avg story points per sprint
#   "is_available": bool,
# }


class AssignmentEngine:
    """
    Scores and ranks developers for a given task, then assigns the best fit.
    """

    # ─── Role compatibility map ───────────────────────────────────────────────
    ROLE_MATCH: dict[str, list[str]] = {
        "backend":   ["backend", "fullstack"],
        "frontend":  ["frontend", "fullstack"],
        "fullstack": ["fullstack", "backend", "frontend"],
        "devops":    ["devops", "fullstack"],
        "qa":        ["qa", "fullstack"],
    }

    # ─── Score weights ────────────────────────────────────────────────────────
    W_ROLE      = 40   # role match is the most important signal
    W_WORKLOAD  = 30   # fewer open tasks = better
    W_VELOCITY  = 20   # higher velocity = better
    W_SKILLS    = 10   # keyword skill match

    MAX_OPEN_TASKS = 8  # a dev with 8+ tasks is considered overloaded

    def assign(
        self,
        task: dict[str, Any],
        developers: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Pick the best available developer for a task.

        Args:
            task:        Task dict with at least 'suggested_role' and 'labels'.
            developers:  List of developer profile dicts.

        Returns:
            The assigned developer dict (with a 'score' key added),
            or None if no suitable developer is found.
        """
        available = [d for d in developers if d.get("is_available", True)]
        if not available:
            logger.warning("[AssignmentEngine] No available developers.")
            return None

        scored = [
            {**dev, "score": self._score(task, dev)}
            for dev in available
        ]

        scored.sort(key=lambda d: d["score"], reverse=True)
        best = scored[0]

        logger.info(
            f"[AssignmentEngine] Task '{task.get('title')}' → "
            f"{best['name']} (score={best['score']})"
        )
        return best

    def assign_bulk(
        self,
        tasks: list[dict[str, Any]],
        developers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Assign multiple tasks, updating simulated workload between assignments
        so the same developer doesn't get everything.

        Returns the task list with 'assigned_to' and 'assignee_name' filled in.
        """
        # Work on a mutable copy of developers
        devs = [dict(d) for d in developers]
        results = []

        for task in tasks:
            assignee = self.assign(task, devs)
            if assignee:
                task = {
                    **task,
                    "assigned_to": assignee["id"],
                    "assignee_name": assignee["name"],
                    "assignment_score": assignee["score"],
                }
                # Increment simulated open_tasks so load balancing works
                for dev in devs:
                    if dev["id"] == assignee["id"]:
                        dev["open_tasks"] = dev.get("open_tasks", 0) + 1
                        break
            else:
                task = {**task, "assigned_to": None, "assignee_name": "Unassigned"}

            results.append(task)

        return results

    # ─── Scoring ─────────────────────────────────────────────────────────────
    def _score(self, task: dict[str, Any], dev: dict[str, Any]) -> float:
        score = 0.0

        # 1. Role match
        required_role  = task.get("suggested_role", "fullstack").lower()
        dev_role       = dev.get("role", "fullstack").lower()
        compatible     = self.ROLE_MATCH.get(required_role, ["fullstack"])
        if dev_role in compatible:
            score += self.W_ROLE
        elif dev_role == "fullstack":
            score += self.W_ROLE * 0.7   # fullstack is always a fallback

        # 2. Workload (fewer open tasks = higher score)
        open_tasks = dev.get("open_tasks", 0)
        if open_tasks >= self.MAX_OPEN_TASKS:
            score += 0   # overloaded — no workload points
        else:
            workload_ratio = 1 - (open_tasks / self.MAX_OPEN_TASKS)
            score += self.W_WORKLOAD * workload_ratio

        # 3. Velocity
        velocity     = dev.get("velocity", 0)
        max_velocity = 60  # story points per sprint ceiling for scoring
        velocity_norm = min(velocity / max_velocity, 1.0)
        score += self.W_VELOCITY * velocity_norm

        # 4. Skill keyword match
        task_labels  = {lbl.lower() for lbl in task.get("labels", [])}
        dev_skills   = {sk.lower() for sk in dev.get("skills", [])}
        matches      = task_labels & dev_skills
        if task_labels:
            skill_ratio = len(matches) / len(task_labels)
            score += self.W_SKILLS * skill_ratio

        return round(score, 2)

    # ─── Workload summary ────────────────────────────────────────────────────
    @staticmethod
    def workload_summary(developers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return a workload overview sorted by open tasks descending."""
        return sorted(
            [
                {
                    "id":         dev["id"],
                    "name":       dev["name"],
                    "role":       dev.get("role", "unknown"),
                    "open_tasks": dev.get("open_tasks", 0),
                    "velocity":   dev.get("velocity", 0),
                    "status":     (
                        "overloaded" if dev.get("open_tasks", 0) >= 8
                        else "busy" if dev.get("open_tasks", 0) >= 5
                        else "available"
                    ),
                }
                for dev in developers
            ],
            key=lambda d: d["open_tasks"],
            reverse=True,
        )


# ─── Singleton ───────────────────────────────────────────────────────────────
assignment_engine = AssignmentEngine()
