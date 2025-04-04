import socket
import threading
import json


class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()

        self.clients = {}
        self.channels = {
            'general': set(),
            'random': set()
        }

        print(f"Server is running on {host}:{port}")

    def broadcast(self, message, channel='general', sender=None):
        """Send message to all clients in a channel"""
        if channel not in self.channels:
            return

        for client in self.channels[channel]:
            if client != sender:  # Don't send back to sender
                try:
                    client.send(message.encode('utf-8'))
                except:
                    # Remove client if unable to send
                    self.remove_client(client)

    def send_private_message(self, message, recipient_nick, sender_socket):
        """Send private message to specific client"""
        for nick, client in self.clients.items():
            if nick == recipient_nick:
                try:
                    client['socket'].send(message.encode('utf-8'))
                    return True
                except:
                    self.remove_client(client['socket'])
        return False

    def remove_client(self, client_socket):
        """Remove client from server records"""
        for nick, client in list(self.clients.items()):
            if client['socket'] == client_socket:
                print(f"{nick} disconnected")
                del self.clients[nick]
                for channel in self.channels.values():
                    if client_socket in channel:
                        channel.remove(client_socket)
                client_socket.close()
                break

    def handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            # Get nickname from client
            nickname = client_socket.recv(1024).decode('utf-8')
            if nickname in self.clients:
                client_socket.send("ERROR: Nickname already in use".encode('utf-8'))
                client_socket.close()
                return

            # Add client to records
            self.clients[nickname] = {
                'socket': client_socket,
                'channel': 'general'
            }
            self.channels['general'].add(client_socket)
            print(f"{nickname} connected")

            # Send welcome message
            welcome_msg = f"SERVER: Welcome to the chat, {nickname}! Type /help for commands."
            client_socket.send(welcome_msg.encode('utf-8'))

            # Notify others
            join_msg = f"SERVER: {nickname} joined the chat!"
            self.broadcast(join_msg, 'general')

            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                # Handle commands
                if message.startswith('/'):
                    if message.startswith('/join '):
                        channel = message.split(' ')[1]
                        if channel not in self.channels:
                            self.channels[channel] = set()
                        self.channels[channel].add(client_socket)
                        self.clients[nickname]['channel'] = channel
                        client_socket.send(f"SERVER: Joined channel {channel}".encode('utf-8'))

                    elif message.startswith('/pm '):
                        parts = message.split(' ', 2)
                        if len(parts) == 3:
                            recipient = parts[1]
                            pm_content = parts[2]
                            pm_msg = f"[PM from {nickname}]: {pm_content}"
                            if self.send_private_message(pm_msg, recipient, client_socket):
                                client_socket.send(f"SERVER: PM sent to {recipient}".encode('utf-8'))
                            else:
                                client_socket.send(f"SERVER: User {recipient} not found".encode('utf-8'))

                    elif message.startswith('/help'):
                        help_msg = """SERVER: Available commands:
/join <channel> - Join a channel
/pm <nickname> <message> - Send private message
/help - Show this help
/quit - Disconnect"""
                        client_socket.send(help_msg.encode('utf-8'))

                    elif message.startswith('/quit'):
                        break
                else:
                    # Regular message
                    full_msg = f"{nickname}: {message}"
                    current_channel = self.clients[nickname]['channel']
                    self.broadcast(full_msg, current_channel, client_socket)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.remove_client(client_socket)
            leave_msg = f"SERVER: {nickname} left the chat!"
            self.broadcast(leave_msg, 'general')

    def start(self):
        """Start accepting client connections"""
        while True:
            client_socket, address = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.start()


if __name__ == "__main__":
    server = ChatServer()
    server.start()