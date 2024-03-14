import paramiko

def ssh_connect_and_exec(host, port, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, port=port, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        print("Command output:", stdout.read().decode().strip())
    except Exception as e:
        print("Error:", e)
    finally:
        ssh.close()

file_path = r'D:\ssh.txt'
password = 'vagrant'

with open(file_path, 'r') as file:
    for line in file:
        host, port = line.strip().split(':')
        ssh_connect_and_exec('192.168.1.42', int(port), 'vagrant', password, 'taskkill /F /IM Te.exe')
