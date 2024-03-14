import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit, QListWidget
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import paramiko
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp

class WorkerSignals(QObject):
    log_updated = pyqtSignal(str)
    ports_ready = pyqtSignal(dict)
    label_updated = pyqtSignal(str)

class Worker(QThread):
    signals = WorkerSignals()

    def __init__(self, hostname, command):
        super().__init__()
        self.hostname = hostname
        self.command = command

    def run(self):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(self.hostname, port=22, username='admin', password='Ltylhfhbev123~')
            powershell_command = f"cd D:/VM ; {self.command}"
            stdin, stdout, stderr = ssh_client.exec_command('powershell -Command "{}"'.format(powershell_command))
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if error:
                self.signals.log_updated.emit("Ошибка: " + error)
            else:
                hosts_ports = self.parse_ssh_config_output(output)
                self.signals.ports_ready.emit(hosts_ports)
                self.signals.label_updated.emit(self.update_label_text(hosts_ports))
        except paramiko.AuthenticationException:
            self.signals.log_updated.emit("Ошибка аутентификации, пожалуйста, проверьте ваши учетные данные.")
        except paramiko.SSHException as e:
            self.signals.log_updated.emit(f"Ошибка SSH соединения: {e}")
        finally:
            ssh_client.close()

    def parse_ssh_config_output(self, output):
        hosts_ports = {}
        lines = output.split('\n')
        current_host = None
        for line in lines:
            if line.startswith("Host"):
                current_host = line.split()[1]
            elif current_host and line.startswith("  Port"):
                port = line.split()[1]
                hosts_ports[current_host] = port
        return hosts_ports

    def update_label_text(self, hosts_ports):
        label_text = "<table>"
        for host, port in hosts_ports.items():
            label_text += f"<tr><td>{host} - порт: {port}</td></tr>"
        label_text += "</table>"
        return label_text

class SSHConfigApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.ports = {}  # Добавляем переменную для хранения портов
        self.initUI()

    def clear_previous_results(self):
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.signals.log_updated.disconnect()
            self.worker.signals.ports_ready.disconnect()
            self.worker.signals.label_updated.disconnect()
            self.worker = None
        self.ports.clear()  # Очищаем словарь с портами
        self.label.clear()  # Очищаем содержимое метки
        self.log_output.clear()  # Очищаем содержимое текстового поля

    def initUI(self):
        self.setWindowTitle('Почувствуй себя богом')
        self.setFixedSize(600, 400)

        self.label = QTextBrowser()
        self.label.setOpenExternalLinks(True)
        self.label.setReadOnly(True)

        self.log_output = QTextBrowser()
        self.log_output.setReadOnly(True)

        self.ip_list = QListWidget()
        self.ip_list.setMaximumWidth(130)
        self.ip_list.addItems(["192.168.1.11", "192.168.1.12", "192.168.1.13", "192.168.1.42", "192.168.1.16", "192.168.1.17", "192.168.1.51"])
        self.ip_list.itemClicked.connect(self.select_ip)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Введите IP адрес")
        ip_validator = QRegExpValidator(QRegExp("([0-9]{1,3}\\.){3}[0-9]{1,3}"), self)
        self.ip_input.setValidator(ip_validator)

        self.get_ports_button = QPushButton('Получить порты')
        self.get_ports_button.clicked.connect(self.get_ports)

        self.process_name_input = QLineEdit()  
        self.process_name_input.setPlaceholderText("Введите имя процесса")

        self.kill_bots_button = QPushButton('Убить ботов')
        self.kill_bots_button.clicked.connect(self.kill_bots)

        input_button_layout = QVBoxLayout()
        input_button_layout.addWidget(self.ip_input)
        input_button_layout.addWidget(self.get_ports_button)
        input_button_layout.addWidget(self.process_name_input)
        input_button_layout.addWidget(self.kill_bots_button)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.ip_list)
        main_layout.addLayout(input_button_layout)

        layout = QVBoxLayout()
        layout.addLayout(main_layout)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def select_ip(self, item):
        ip = item.text()
        self.ip_input.setText(ip)

    def get_ports(self):
        if self.worker is not None and self.worker.isRunning():
            self.log_output.append("Задача уже выполняется.")
        else:
            hostname = self.ip_input.text().strip()
            if not hostname:
                self.log_output.append("Введите IP адрес.")
                return

            command = "vagrant ssh-config"

            self.clear_previous_results()  # Очищаем предыдущие результаты перед получением новых портов

            self.get_ports_button.setEnabled(False)

            self.worker = Worker(hostname, command)
            self.worker.signals.log_updated.connect(self.update_log)
            self.worker.signals.ports_ready.connect(self.save_ports)
            self.worker.signals.label_updated.connect(self.update_label)  
            self.worker.finished.connect(lambda: self.get_ports_button.setEnabled(True))
            self.worker.start()

    def update_log(self, text):
        self.log_output.append(text)

    def update_label(self, text):
        self.label.setHtml(text)

    def save_ports(self, ports):
        self.ports = ports
        self.log_output.append("Порты получены.")

    def kill_bots(self):
        if not self.ports:
            self.log_output.append("Порты не получены. Сначала выполните 'Получить порты'.")
            return

        process_name = self.process_name_input.text().strip()
        if not process_name:
            self.log_output.append("Введите имя процесса.")
            return

        self.log_output.clear()
        password = 'vagrant'
        for port in self.ports.values():
            command = f"taskkill /F /IM {process_name}.exe"
            result = self.ssh_connect_and_exec(self.ip_input.text().strip(), int(port), 'vagrant', password, command)
            self.log_output.append(f"Результат для порта {port}: {result}")

    def ssh_connect_and_exec(self, host, port, username, password, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostname=host, port=port, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode('utf-8').strip()
            return result
        except Exception as e:
            print("Ошибка:", e)
            return str(e)
        finally:
            ssh.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SSHConfigApp()
    ex.show()
    sys.exit(app.exec_())
