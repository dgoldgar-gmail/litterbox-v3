import subprocess
import os
import logging
from config import Configuration
from git_client import GitClient
from flask import Blueprint, jsonify, request, render_template

configuration = Configuration()
git_client = GitClient(".")

git_manager_bp = Blueprint('git_manager', __name__)
logger = logging.getLogger(__name__)

# The path to the repository we want to manage
REPO_PATH = os.environ.get("GIT_REPO_PATH", configuration.GIT_REPO_PATH)

@git_manager_bp.route('/index', methods=['GET'])
def index():
    return render_template('git_manager/index.html', status_data=git_status_data())

@git_manager_bp.route('/commit', methods=['POST'])
def commit():
    data = request.get_json() or {}
    selected_files = data.get('files', [])
    message = data.get("message", "Update from Litterbox UI")
    logger.info(f"input: {data}")
    logger.info(f"message: {message}")

    for file in data['files']:
        logger.info(f"Processing file: {file['path']} ({file['status']})")
        if file['status'] == 'A':
            git_client.add(file['path'])
        if file['status'] == 'D':
            git_client.add(file['path'])
        elif file['status'] == 'M':
            git_client.add(file['path'])

    new_commit = git_client.commit(message)
    commit_info = {
        "hash": new_commit.hexsha,
        "short_hash": new_commit.hexsha[:7],
        "message": new_commit.message,
        "author": new_commit.author.name
    }

    logger.debug(f"COMMIT: {commit_info}")

    return jsonify({
            "success": True,
            "commit_result": commit_info,
            "status_data": git_status_data()
            })

@git_manager_bp.route('/push', methods=['POST'])
def push():
    data = request.get_json() or {}
    is_force = data.get('force', False)

    current_branch = git_client.current_branch
    # push_results is now a list: [{"branch": "...", "success": True, ...}]
    push_results = git_client.push(is_force)

    logger.debug(f"PUSH RESULT for {current_branch}: {push_results}")

    branch_result = next((item for item in push_results if item["branch"] == current_branch), None)

    if branch_result:
        is_success = branch_result["success"]
        message = branch_result["summary"]
    else:
        is_success = all(res["success"] for res in push_results) if push_results else False
        message = "Push completed" if is_success else "Push failed or no results returned"

    return jsonify({
        "success": is_success,
        "message": message,
        "push_results": push_results,
        "status_data": git_status_data()
    })

@git_manager_bp.route('/squash', methods=['POST'])
def squash():

    data = request.get_json() or {}
    message = data.get("message", "Squashed from Litterbox UI")

    squash_result = git_client.squash_since_divergence(message)

    logger.info(f"SQUASH RESULT: {squash_result}")

    return jsonify({
        "success": squash_result.get("success", False),
        "message": squash_result.get("message", "Squash completed"),
        "status_data": git_status_data()
    })

@git_manager_bp.route('/reset', methods=['POST'])
def reset_work_route():
    data = request.get_json() or {}
    mode = data.get('mode', 'soft')
    files = data.get('files', [])

    # Validation: If 'files' mode is chosen, we need a list
    if mode == 'files' and not files:
        return jsonify({
            "success": False,
            "message": "No files specified for reset."
        }), 400

    try:
        # Call your git_client method
        result_msg = git_client.reset_work(mode=mode, files=files)

        return jsonify({
            "success": True,
            "message": result_msg,
            "status_data": git_status_data() # Refresh UI state (files, log, etc)
        }), 200

    except Exception as e:
        logger.error(f"Reset failed ({mode}): {e}")
        return jsonify({
            "success": False,
            "message": f"Git error: {str(e)}"
        }), 500

@git_manager_bp.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json() or {}
    branch_name = data.get('branch_name')
    create = data.get('create', False)

    branch_exists = branch_name in git_client.repo.branches

    try:
        git_client.switch_branch(branch_name, create)
        if create and not branch_exists:
            message = f"Created and switched to branch '{branch_name}'"
        else:
            message = f"Switched to branch '{branch_name}'"

        return jsonify({
            "success": True,
            "message": message,
            "status_data": git_status_data()
        }), 200

    except Exception as e:
        # If switch_branch fails (e.g., merge conflicts, git lock), we catch it here
        return jsonify({
            "success": False,
            "message": f"Failed to switch to {branch_name}: {str(e)}",
            "status_data": git_status_data()
        }), 500

def git_status_data():
    git_client.current_branch
    result = {}
    result['branch'] = git_client.current_branch
    #result['is_dirty'] = git_client.is_dirty()
    result['untracked'] = git_client.git_untracked()
    result['unstaged'] = git_client.git_unstaged()
    result['staged'] = git_client.git_staged()
    result['committed'] = git_client.git_committed()
    result['unstaged_diff'] = git_client.git_unstaged_diff()
    result['staged_diff'] = git_client.git_staged_diff()
    result['committed_diff'] = git_client.git_committed_diff()
    result['branches'] = git_client.git_branches()
    result['log'] = git_client.git_log()
    logger.debug(result)
    return result
