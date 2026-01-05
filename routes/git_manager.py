import subprocess
import os
import logging
from config import GIT_REPO_PATH
from flask import Blueprint, jsonify, request, render_template

git_manager_bp = Blueprint('git_manager', __name__)
logger = logging.getLogger(__name__)

# The path to the repository we want to manage
REPO_PATH = os.environ.get("GIT_REPO_PATH", GIT_REPO_PATH)

@git_manager_bp.route('/index', methods=['GET'])
def index():
    result = git_api_status()
    logger.info(f"RESULT: {result}")
    return render_template('git_manager/index.html', status_data=result)

@git_manager_bp.route('/commit', methods=['POST'])
def commit():
    data = request.get_json() or {}
    selected_files = data.get('files', [])
    message = data.get("message", "Update from Litterbox UI")
    logger.info(f"input: {data}")
    logger.info(f"message: {message}")

    for file in data['files']:
        logger.info(f"Processing file: {file['path']} ({file['status']})")


        if file['status'] == 'modified':
            run_git_command(["add", file['path']])
        elif file['status'] == 'untracked':
            run_git_command(["add", file['path']])
        elif file['status'] == 'deleted':
            run_git_command(["add", file['path']])


    commit = run_git_command(["commit", "-m", message])
    #push = run_git_command(["push", "origin", "main"])

    logger.info(f"COMMIT: {commit}")
    #logger.info(f"PUSH: {push}")

    status_data = git_api_status()
    logger.info(f"STATUS: {status_data}")
    return jsonify({
        "success": commit["success"],
        "status_data": status_data,
        "files_processed": selected_files,
        "diff_data": ""
    })

@git_manager_bp.route('/push', methods=['POST'])
def push():
    push = run_git_command(["push", "origin", "main"])

    logger.info(f"COMMIT: {push}")

    status_data = git_api_status()
    logger.info(f"STATUS: {status_data}")
    return jsonify({
        "success": push["success"],
        "status_data": status_data,
        "diff_data": ""
    })

@git_manager_bp.route('/diff', methods=['POST'])
def diff():
    data = request.get_json() or {}
    selected_files = data.get('files', [])

    logger.info(f"User wants diff for: {selected_files}")

    if not selected_files:
        return jsonify({"success": False, "error": "No files selected"}), 400

    diff_data = [run_git_command(["diff", f]) for f in selected_files]
    logger.info(f"Diff results: {diff_data}")

    status_data = git_api_status()
    return jsonify({
        "success": True,
        "status_data": status_data,
        "files_processed": selected_files,
        "diff_data": diff_data
    })

@git_manager_bp.route('/pull', methods=['POST'])
def pull():
    result = run_git_command(["pull", "origin", "main"])

    status_data = git_api_status()
    return jsonify({
        "success": True,
        "status_data": result,
        "diff_data": ""
    })

@git_manager_bp.route('/staged', methods=['POST'])
def staged():
    staged_data = run_git_command(["diff", "origin/main..HEAD"])
    logger.info(f"RESULT: {staged_data}")

    status_data = git_api_status()
    return jsonify({
        "success": status_data['success'],
        "status_data": status_data,
        "staged_data": staged_data['stdout'],
        "diff_data": ""
    })

@git_manager_bp.route('/checkout', methods=['POST'])
def checkout():
    result = run_git_command(["checkout", "."])
    logger.info(f"RESULT: {result}")
    status_data = git_api_status()
    return jsonify({
        "success": result['success'],
        "status_data": status_data,
        "diff_data": ""
    })

@git_manager_bp.route('/reset', methods=['POST'])
def reset():
    fetch_result =run_git_command(["fetch", "origin"])
    reset_result = run_git_command(["reset", "--hard", "origin/main"])
    logger.info(f"RESULT: {reset_result}")
    status_data = git_api_status()
    return jsonify({
        "success": fetch_result['success'],
        "status_data": status_data,
        "diff_data": ""
    })

def git_api_status():

    porcelain_res = run_git_command(["status", "--porcelain"])
    branch_res = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    run_git_command(["fetch", "origin"])
    count_res = run_git_command(["rev-list", "--left-right", "--count", "HEAD...origin/main"])
    stdout_str = porcelain_res.get("stdout", "") if porcelain_res else ""
    files = parse_porcelain_status(stdout_str)
    branch = branch_res.get("stdout", "unknown").strip() if branch_res else "unknown"
    ahead, behind = 0, 0
    if count_res and count_res.get("success"):
        counts = count_res.get("stdout", "0 0").strip().split()
        if len(counts) >= 2:
            ahead = counts[0].strip()
            behind = counts[1].strip()
    return {
        "success": True,
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "changes": files,
        "is_dirty": len(files) > 0
    }


def parse_porcelain_status(stdout):
    """
    Parses 'git status --porcelain' output.
    Format is XY PATH where XY are status codes.
    """
    files = []
    if not stdout:
        return files

    mapping = {
        'M': 'modified',
        'A': 'added',
        'D': 'deleted',
        'R': 'renamed',
        'C': 'copied',
        'U': 'updated but unmerged',
        '?': 'untracked',
        '!': 'ignored',
        ' ': 'unchanged'
    }

    for line in stdout.splitlines():
        # Lines should be "XY path" (at least 4 chars)
        if len(line) < 4:
            continue

        index_status = line[0]
        work_tree_status = line[1]

        # Slicing from index 3 captures the path exactly as Git provides it
        raw_path = line[3:]

        # Handle renames: "old_path -> new_path"
        if " -> " in raw_path:
            file_path = raw_path.split(" -> ")[-1].strip()
        else:
            file_path = raw_path.strip()

        files.append({
            "path": file_path,
            "index": mapping.get(index_status, "unchanged"),
            "working_tree": mapping.get(work_tree_status, "unchanged"),
            "raw_code": f"{index_status}{work_tree_status}"
        })
    return files

def run_git_command(args):
    """Helper to run git commands via system binary."""
    try:
        if not os.path.exists(REPO_PATH):
            os.makedirs(REPO_PATH, exist_ok=True)

        result = subprocess.run(
            ["git"] + args,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            timeout=30,
            env=os.environ
        )
        return {
            "success": result.returncode == 0,
            # CRITICAL: We do NOT strip() stdout here because porcelain status
            # depends on the exact column positions.
            "stdout": result.stdout,
            "stderr": result.stderr.strip(),
            "rc": result.returncode
        }
    except Exception as e:
        logger.error(f"Execution Error: {str(e)}")
        return {"success": False, "stdout": "", "stderr": str(e), "rc": 1}
