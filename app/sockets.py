import json
import socketserver
import threading
import datetime
from app.models import Machine, User


def set_sys_details(sys_details, m):
    sys_details.pop("mac")
    sys_details.pop("type")
    m.sys_details = sys_details
    return True


def check_sys_details(sys_details_input, m):
    for key in m.sys_details.keys():  # Check the values for each key match
        if m.sys_details[key] != sys_details_input[key]:
            set_sys_details(sys_details_input, m)

    if not m.sys_details.keys():
        set_sys_details(sys_details_input, m)

    return True


def add_sys_status(time, sys_status, m):
    cpu = sys_status.pop("cpu usage", None)
    dsk = sys_status.pop("disk usage", None)
    mem = sys_status.pop("memory usage", None)
    m.sys_status = [time, cpu, dsk, mem]


def timestamp(dt=None):
    if not dt:
        dt = datetime.datetime.now()
    seconds = -round(dt.microsecond / int("1" + len(str(dt.microsecond)) * "0"))
    dt = dt - datetime.timedelta(0, seconds, dt.microsecond)
    second = 15 * round(dt.second / 15)
    if second == 60:
        second = 0
        minute = dt.minute + 1
        if minute == 60:
            minute = 0
            hour = dt.hour + 1
            if hour == 24:
                hour = 0
        else:
            hour = dt.hour
    else:
        minute = dt.minute
        hour = dt.hour
    dt = dt.replace(hour=hour, minute=minute, second=second)
    return int(dt.timestamp() * 1000)


class ServerRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        dt = timestamp()
        data_json = self.request.recv(4096).strip()
        data = json.loads(data_json)

        mac = data.get("mac", None)
        if not mac:
            self.request.sendall("err 1: No MAC address supplied.".encode("ascii"))
            return 1

        key = data.pop("secret", None)

        if data["type"] == "setup":
            username = data.get("username", None)
            u = User.query().filter(User.username == username).first()
            if u:
                new = Machine(mac, u.id, data.get("nickname", None))
                new.save()
                return 0
            string = f"err 4: No user exists with username: '{username}'"
            self.request.sendall(string.encode("ascii"))
            return 4

        else:

            m = Machine.query().filter(Machine.mac_address == mac).first()
            if not m:
                string = "err 2: No machine with supplied mac registered."
                self.request.sendall(string.encode("ascii"))
                return 2

            elif m.secret_key and m.secret_key != key:
                string = "err 3: Key supplied doesn't match the one stored."
                self.request.sendall(string.encode("ascii"))
                return 3

            if data["type"] == "sys_details":
                check_sys_details(data, m)
                command_sender(m, self.request)
                return 0

            elif data["type"] == "sys_status":
                add_sys_status(dt, data, m)
                command_sender(m, self.request)
                return 0

            elif data["type"] == "cmd_out":
                if data.get("output", None):
                    m.output = f'"{data.get("command")},{data.get("output")}"'
                    command_sender(m, self.request)
                    return 0
                self.request.sendall("err 6: No output supplied")
                return 6

        return 5


def command_sender(m, request) -> None:
    command = m.command
    if command:
        request.sendall(f"cmd:{command}".encode("ascii"))
        del m.command


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass  # Just use inherit from ThreadingMixIn and TCPServer, no need for any editing


def server_thread_getter(port, addr="localhost"):  # By using a getter we can still supply a port in the app factory
    server = ThreadedTCPServer((addr, port), ServerRequestHandler)
    s_thread = threading.Thread(target=server.serve_forever)
    return s_thread


if __name__ == "__main__":
    server_thread = server_thread_getter(16969)
    server_thread.start()
