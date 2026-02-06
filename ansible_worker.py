import logging
import time
import json
import os
import tempfile
import subprocess
from pathlib import Path
import ansible_runner
from pathlib import Path

#from config import ANSIBLE_VAULT_PASS_PATH
#VAULT_PASS_FILE = Path(ANSIBLE_VAULT_PASS_PATH)
#raw_vault_pass = VAULT_PASS_FILE.read_text().strip()

BASE_DIR = Path(__file__).resolve().parent
RUNNER_DIR = BASE_DIR / "ansible"
PROJECT_DIR = RUNNER_DIR / "project"
QUEUE_DIR = RUNNER_DIR / "queue"
RESULTS_DIR = RUNNER_DIR / "results"

QUEUE_DIR.mkdir(exist_ok=True, parents=True)
RESULTS_DIR.mkdir(exist_ok=True, parents=True)

logger = logging.getLogger(__name__)

def run_job(job_file: Path):
    with job_file.open() as f:
        job = json.load(f)

    job_id = job_file.stem
    host = job.get("host")
    tag = job.get("tag")
    playbook_name = job.get("playbook", "site.yml")
    extravars = job.get("extravars", {})

    logger.info(f"[worker] Starting job {job_id} | Host: {host} | Tags: {tag}")

    ansible_config = PROJECT_DIR / "ansible.cfg"
    ansible_log_path = RUNNER_DIR / "logs" / "ansible.log"
    ansible_vault_password_file = BASE_DIR / ".ansible" / "vault_pass"
    ansible_inventory_path = RUNNER_DIR / "inventory" / "hosts.yml"

    logger.info(f"ansible_config: {ansible_config}")
    logger.info(f"ansible_inventory_path: {ansible_inventory_path}")
    logger.info(f"ansible_log_path: {ansible_log_path}")
    logger.info(f"ansible_vault_password_file: {ansible_vault_password_file}")

    env_vars = {
        "ANSIBLE_PYTHON_INTERPRETER": "auto_silent",
        "ANSIBLE_FORCE_COLOR": "True",
        "ANSIBLE_STDOUT_CALLBACK": "debug",
        "ANSIBLE_CONFIG": str(ansible_config),
        "ANSIBLE_LOG_PATH": str(ansible_log_path),
        "ANSIBLE_VAULT_PASSWORD_FILE": str(ansible_vault_password_file)
    }

    r = ansible_runner.run(
        private_data_dir=str(RUNNER_DIR),
        playbook=playbook_name,
        inventory=str(ansible_inventory_path),
        extravars=extravars,
        limit=host,
        tags=tag,
        ident=job_id,
        quiet=False,
        verbosity=2, # TODO: Make this configurable
        settings={
            "timeout": 0,
            "process_isolation": False
        },
        envvars=env_vars
    )

    process_results(job_id, r)

def process_results(job_id, r):
    stats = r.stats if r.stats is not None else {}

    # Logic to fix 'canceled' status when the playbook actually succeeded
    total_failures = sum(stats.get('failures', {}).values())
    total_unreachable = sum(stats.get('unreachable', {}).values())

    final_status = r.status
    # If it says canceled but the RECAP shows no failures, it's a success
    if r.status == 'canceled' and total_failures == 0 and total_unreachable == 0:
        final_status = 'successful'
    # If the runner finished but we have failures, it's failed
    elif total_failures > 0 or total_unreachable > 0:
        final_status = 'failed'

    result = {
        "status": final_status,
        "rc": r.rc,
        "stats": stats,
    }

    result_file = RESULTS_DIR / f"{job_id}.json"
    result_file.write_text(json.dumps(result, indent=2))
    logger.info(f"[worker] Finished job {job_id}. Status: {final_status}")

def main():
    logger.info(f"[worker] Monitoring {QUEUE_DIR}...")
    while True:
        jobs = sorted(QUEUE_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime)
        for job_file in jobs:
            try:
                run_job(job_file)
            except Exception as e:
                logger.error(f"[worker] ERROR: {e}")
            finally:
                if job_file.exists():
                    job_file.unlink()
        time.sleep(2)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    main()
