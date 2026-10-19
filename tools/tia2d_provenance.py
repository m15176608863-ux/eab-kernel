"""Optional Git provenance; exact working-file manifests remain authoritative."""
import subprocess
from pathlib import Path


def git_provenance(root):
    """An exported source tree is supported, not a failed Git checkout."""
    try:
        top = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=root,
            stderr=subprocess.DEVNULL, text=True).strip()
        if Path(top).resolve() != Path(root).resolve():
            return dict(git_commit=None, git_commit_reason="no_git_checkout")
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
            stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return dict(git_commit=None, git_commit_reason="no_git_checkout")
    return dict(git_commit=commit,
                git_commit_reason="working_tree_source_manifest_authoritative")
