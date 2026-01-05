import subprocess

def execute_command(command_array=None, returnLines=False, returnStdout=False):
  process = subprocess.Popen( command_array,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)
  if returnLines == False and returnStdout == False:
    stdout, stderr = process.communicate()
    exit_code = process.wait()
    return stdout.decode("utf-8")
  elif returnStdout == True:
    stdout, stderr = process.communicate()
    exit_code = process.wait()
    return stderr.decode("utf-8")
  else:
    log.debug(str(command_array) )
    return process.stdout.readlines()


def execute_command_over_ssh(command_array=None, target_host=None, username="root", returnLines=False, returnStdout=False):
  ssh_command_array = ["/usr/bin/ssh", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", username + "@"+target_host ]
  # -o PubkeyAcceptedKeyTypes=ssh-rsa
  ssh_command_array.extend(command_array)
  return execute_command(ssh_command_array, returnLines, returnStdout)
