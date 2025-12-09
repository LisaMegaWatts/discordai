import os
from github import Github
from github.GithubException import GithubException

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # Format: "owner/repo"

def create_feature_branch_and_pr(feature_title, feature_description, discord_link):
    """
    Automates creation of a feature branch and pull request in GitHub.
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise ValueError("GITHUB_TOKEN and GITHUB_REPO must be set in environment.")

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    # Generate branch name
    branch_name = f"feature/{feature_title.lower().replace(' ', '_')}"
    try:
        main_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
    except GithubException as e:
        if "Reference already exists" not in str(e):
            raise

    # Create commit (stub file for MVP)
    file_path = f"features/{branch_name}.md"
    commit_message = f"Add feature request: {feature_title}"
    content = f"# Feature Request\n\n**Title:** {feature_title}\n\n**Description:**\n{feature_description}\n\n**Discord Link:** {discord_link}\n"
    try:
        repo.create_file(file_path, commit_message, content, branch=branch_name)
    except GithubException as e:
        if "already exists" not in str(e):
            raise

    # Create PR
    pr_title = f"Feature: {feature_title}"
    pr_body = f"{feature_description}\n\nOriginal Discord request: {discord_link}"
    pr = repo.create_pull(
        title=pr_title,
        body=pr_body,
        head=branch_name,
        base="main"
    )
    return pr.html_url