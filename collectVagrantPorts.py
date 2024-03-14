import paramiko

def execute_ssh_command(hostname, port, username, password, command, output_file):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname, port=port, username=username, password=password)
        
        powershell_command = f"cd D:/VM ; {command}"
        stdin, stdout, stderr = ssh_client.exec_command('powershell -Command "{}"'.format(powershell_command))

        output = stdout.read().decode()

        err = stderr.read().decode()
        if err:
            print("Error:", err)

        hosts, ports = parse_ssh_config_output(output)
        with open(output_file, 'a') as file:
            for host, port in zip(hosts, ports):
                file.write(f"{host}:{port}\n")
        print(f"Saved SSH configuration to {output_file}")
    except paramiko.AuthenticationException:
        print("Authentication failed, please check your credentials.")
    except paramiko.SSHException as ssh_exception:
        print(f"SSH connection failed: {ssh_exception}")
    finally:
        ssh_client.close()

def parse_ssh_config_output(output):
    hosts = []
    ports = []
    lines = output.split('\n')
    host = None
    port = None
    for line in lines:
        if line.startswith("Host "):
            if host:
                hosts.append(host)
                ports.append(port)
            host = line.split()[1]
            port = None
        elif "HostName" in line:
            port = line.split()[1]
        elif "Port" in line:
            port = line.split()[1]
    if host:
        hosts.append(host)
        ports.append(port)
    return hosts, ports

if __name__ == "__main__":
    hosts = [
             "192.168.1.11",
             "192.168.1.12",
             "192.168.1.16",
             "192.168.1.13",
             "192.168.1.42",
             "192.168.1.17",
             "192.168.1.51"
             ]
    ports = [22, 22, 22, 22, 22, 22]
    username = "admin"
    password = "Ltylhfhbev123~"
    command = "vagrant ssh-config"
    output_file = "D:/ssh.txt"

    with open(output_file, 'w') as file:
        pass

    for host, port in zip(hosts, ports):
        print("Connecting to", host)
        execute_ssh_command(host, port, username, password, command, output_file)
        print()
