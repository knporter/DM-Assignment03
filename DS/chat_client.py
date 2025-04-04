import socket
import threading
import json


class ChatClient:
    def __init__(self):
        self.nickname = ''
        self.server_address = ''
        self.current_channel = 'general'
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self, server_ip, server_port):
        """Connect to the chat server"""
        try:
            self.server_address = (server_ip, server_port)
            self.client_socket.connect(self.server_address)
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def set_nickname(self, nickname):
        """Set nickname and send to server"""
        self.nickname = nickname
        try:
            self.client_socket.send(nickname.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            if response.startswith("ERROR"):
                print(response)
                return False
            return True
        except Exception as e:
            print(f"Error setting nickname: {e}")
            return False

    def receive_messages(self):
        """Handle incoming messages from server"""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(message)
            except:
                print("Disconnected from server")
                self.client_socket.close()
                break

    def send_message(self, message):
        """Send message to server"""
        try:
            self.client_socket.send(message.encode('utf-8'))
        except:
            print("Failed to send message")

    def start(self):
        """Start the client interface"""
        print("Welcome to the chat client!")

        # Get server details
        server_ip = input("Enter server IP (default: localhost): ") or 'localhost'
        server_port = int(input("Enter server port (default: 5555): ") or 5555)

        if not self.connect_to_server(server_ip, server_port):
            return

        # Get nickname
        while True:
            nickname = input("Choose your nickname: ")
            if self.set_nickname(nickname):
                break

        # Start receive thread
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        # Handle user input
        print("Type /help for available commands")
        while True:
            message = input()
            if message.lower() == '/quit':
                self.send_message('/quit')
                break
            self.send_message(message)

        self.client_socket.close()
        print("Disconnected from chat server")


if __name__ == "__main__":
    client = ChatClient()
    client.start()