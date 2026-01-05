import logging
import paramiko
import logging
import urllib3
from config import KEY_FILE, SSH_USER
from pathlib import Path
from scp import SCPClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
logger.propagate = True

def get_ssh_client(host):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, 22, SSH_USER, key_filename=KEY_FILE)
    return client


def copy_to_remote(host, local_file, remote_file):
    client = None
    scp = None
    try:
        client = get_ssh_client(host)
        logging.info(f"Provisioning file to remote host.")
        logging.info(f"scp {local_file} {host}:{remote_file}")

        client = get_ssh_client(host)
        remote_path=Path(remote_file).parent
        command = f"mkdir -p {remote_path}"
        logger.info(f"Executing command: {command}")
        stdin, stdout, stderr = client.exec_command(command, get_pty=True, bufsize=0)
        for line in iter(stdout.readline, ""):
            logger.info(line)
        scp = SCPClient(client.get_transport())
        scp.put(local_file, remote_file)

    except Exception as e:
        logging.info(f"Copy to remote failed for {local_file} from remote host {host}: {e}")
    finally:
        if scp != None:
            scp.close()
        if client != None:
            client.close()
            
def copy_from_remote(host, remote_file, local_file):
    client = None
    scp = None
    try:
        logging.info("Backing up remote file.")
        logging.info(f"scp {host}:{remote_file} {local_file}")
        logging.info(f"Making backup directory {Path(local_file).parent}")
        Path(local_file).parent.mkdir(parents=True, exist_ok=True)
        client = get_ssh_client(host)
        scp = SCPClient(client.get_transport())
        scp.get(remote_file, local_file)
    except Exception as e:
        logging.info(f"Copy from remote failed for {local_file} remote host {host}: {e}")
    finally:
        if scp != None:
            scp.close()
        if client != None:
            client.close()