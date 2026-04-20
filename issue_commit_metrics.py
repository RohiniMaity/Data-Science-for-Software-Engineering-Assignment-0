#!/usr/bin/env python3

import os
from pydriller import Repository
from pydriller.domain.commit import ModificationType


ISSUE_IDS = {
    "LUCENE-12",
    "LUCENE-17",
    "LUCENE-701",
    "LUCENE-1200",
    "LUCENE-1799",
}

VALID_CHANGE_TYPES = {
    ModificationType.ADD,
    ModificationType.MODIFY,
    ModificationType.DELETE,
}


def normalize_issue_id(issue_id: str) -> str:
    return issue_id.strip().upper()


def safe_number(value):
    return value if value is not None else 0.0


def get_valid_modified_paths(commit):
    paths = set()

    for mf in commit.modified_files:
        if mf.change_type in VALID_CHANGE_TYPES:
            path = mf.new_path if mf.new_path else mf.old_path
            if path:
                paths.add(path)

    return paths


def collect_unique_commits(repo_path, issue_ids):
    normalized_issue_ids = {normalize_issue_id(i) for i in issue_ids}
    matched_commits = []
    seen_hashes = set()

    for commit in Repository(repo_path).traverse_commits():
        msg = (commit.msg or "").upper()

        if any(issue_id in msg for issue_id in normalized_issue_ids):
            if commit.hash not in seen_hashes:
                seen_hashes.add(commit.hash)
                matched_commits.append(commit)

    return matched_commits


def compute_combined_metrics(commits):
    total_commits = len(commits)

    if total_commits == 0:
        return {
            "total_commits": 0,
            "total_unique_files_changed": 0,
            "average_unique_files_changed": 0.0,
            "total_dmm_score": 0.0,
            "average_dmm_metrics": 0.0,
        }

    total_unique_files_changed = 0
    total_dmm_score = 0.0

    for commit in commits:
        valid_paths = get_valid_modified_paths(commit)
        total_unique_files_changed += len(valid_paths)

        dmm_size = safe_number(commit.dmm_unit_size)
        dmm_complexity = safe_number(commit.dmm_unit_complexity)
        dmm_interfacing = safe_number(commit.dmm_unit_interfacing)

        total_dmm_score += (dmm_size + dmm_complexity + dmm_interfacing)

    average_unique_files_changed = total_unique_files_changed / total_commits
    average_dmm_metrics = total_dmm_score / total_commits

    return {
        "total_commits": total_commits,
        "total_unique_files_changed": total_unique_files_changed,
        "average_unique_files_changed": average_unique_files_changed,
        "total_dmm_score": total_dmm_score,
        "average_dmm_metrics": average_dmm_metrics,
    }


def main():
    repo_path = "./lucene"

    if not os.path.exists(repo_path):
        print(f"Repository path does not exist: {repo_path}")
        print("Clone the repository first:")
        print("git clone https://github.com/apache/lucene.git")
        return

    commits = collect_unique_commits(repo_path, ISSUE_IDS)
    metrics = compute_combined_metrics(commits)

    print("Issue IDs considered:")
    for issue_id in sorted(ISSUE_IDS):
        print(f"  - {issue_id}")

    print("\n=== Combined Results ===")
    print(f"Total unique commits found: {metrics['total_commits']}")
    print(f"Total unique files changed across all commits: {metrics['total_unique_files_changed']}")
    print(f"Average Unique Files Changed: {metrics['average_unique_files_changed']:.4f}")
    print(f"Total DMM score across all commits: {metrics['total_dmm_score']:.4f}")
    print(f"Average DMM Metrics: {metrics['average_dmm_metrics']:.4f}")

    print("\nMatched commit hashes:")
    for commit in commits:
        print(commit.hash)


if __name__ == "__main__":
    main()