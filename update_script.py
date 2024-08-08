import os
import subprocess

def update_repo():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        # Fetch latest changes from the remote repository
        subprocess.run(["git", "pull"], cwd=repo_dir, check=True)
        print("Repository updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update the repository: {e}")
        return False
    return True

if __name__ == "__main__":
    update_repo()
