from sshtunnel import open_tunnel
from time import sleep

with open_tunnel(
    ('173.82.143.46', 22),
    ssh_username="root",
    ssh_password="Hanhphuc1q2",
    remote_bind_address=('127.0.0.1', 43837)
) as server:

    print(server.local_bind_port)
    while True:
        # press Ctrl-C for stopping
        sleep(1)

print('FINISH!')
