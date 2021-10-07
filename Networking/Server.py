import time
import socket
import select
import inspect


def merge_dicts(a: dict, b: dict):
    """Merges two dicts. In case of an overlap b will win."""
    return {**a, **b}


class Message:
    messages_to_send = []
    SERVER_SOCKET = None

    def __init__(self, address, message):
        self.address = address
        self.message = message
        self.messages_to_send.append(self)

    def send(self):
        """Send a message to self.socket"""
        self.SERVER_SOCKET.sendto(self.message, self.address)
        self.messages_to_send.remove(self)

    @classmethod
    def remove_messages_to(cls, socket_):
        """Removes all the waiting messages for a specific user"""
        cls.messages_to_send = [msg for msg in cls.messages_to_send if not msg.socket == socket_]


class FalseDict(dict):
    """
    Dictionary that returns false instead of raising KeyError if key is not found
    """

    def __getitem__(self, item):
        try:
            return super(FalseDict, self).__getitem__(item)
        except KeyError:
            return False


class User:
    users_list = {}

    @property
    def current_keys(self):
        return [i for i in self.active_keys if self.active_keys[i]]

    def __init__(self, socket_, address):
        self.socket = socket_
        self.address = address
        self.users_list[self.socket] = self
        self.attributes = {}
        self.active_keys = FalseDict()

    def disconnect(self):
        """Disconnects a user safely."""
        self.users_list.pop(self.socket)
        self.socket.close()

    def __hash__(self):
        return self.address.__hash__()

    def __eq__(self, other):
        if isinstance(other, User):
            return self.address == other.address
        return NotImplemented

    def add_attribute(self, value, protected, name, convert_from_string=lambda x: x):
        """
        Adds an attributes.
        :param value: Value of the attribute
        :param protected: (bool) A protected value can't be changed by the User's client.
        :param name: The name of the attribute
        :param convert_from_string: A function to decode the value from it's string version that is sent over a socket
        """
        self.attributes[name] = Attribute(value, protected, name, convert_from_string)

    def set_attribute(self, name, value):
        """Sets a new value to an attribute name"""
        self.attributes[name].set_value(value)

    def set_keys(self, keys: dict):
        """Sets the current active keys of a user"""
        self.active_keys = keys

    def __getattr__(self, item):
        try:
            return super(User, self).__getattr__(item)
        except AttributeError:
            return self.attributes[item].value

    def replace(self, user_class: type, **kwargs):
        """Replace a certain user with another User class"""
        new = user_class(self.socket, self.address, **kwargs)
        new.set_keys(self.active_keys)
        self.users_list[self.socket] = new
        del self


class Attribute:
    def __init__(self, value, protected, name, convert_from_string=lambda x: x):
        self.value = value
        self.protected = protected
        self.name = name
        self.converter = convert_from_string

    def set_value(self, value, override_permission):
        """
        Sets the value of the attributes
        :param value:
        :param override_permission:
        :return:
        """
        if override_permission or not self.protected:
            self.value = self.converter(value)


class ExampleUser(User):
    def __init__(self, socket_, address, *, username, phone_number):
        super(ExampleUser, self).__init__(socket_, address)
        self.add_attribute(username, False, 'username')
        self.add_attribute(phone_number, False, 'phone_number', int)


class MetaServer(type):
    def __new__(mcs, name, bases, attrs):
        """Makes sure commands are inherited"""
        cls = type.__new__(mcs, name, bases, attrs)
        if 'commands' in attrs:
            dictionary = attrs['commands']
            if not isinstance(dictionary, dict):
                raise AttributeError('"commands" attribute must be of type "dict"')
            for base in cls.__bases__:
                try:
                    if issubclass(base, CommandServer):
                        print(cls.commands, base.commands)
                        cls.commands = {**cls.commands, **base.commands}  # inheriting the commands
                except NameError:  # CommandServer is not yet maid
                    pass
        for attr in attrs:
            function = filter(lambda f: f.__name__ == attr, cls.commands.values())
            try:
                function = next(function)
                for key, value in cls.commands.items():
                    if value is function:
                        cls.commands[key] = attrs[attr]
            except StopIteration:
                pass
        return cls


class CommandServer(metaclass=MetaServer):
    TICKS_PER_SECOND = 60
    PORT = 35241
    IP = "0.0.0.0"

    open_client_sockets = []

    commands = {}

    instance = None

    is_server = True

    def __init__(self):
        CommandServer.instance = self
        self.server_socket = socket.socket()
        self.server_socket.setblocking(False)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen(1000)
        self.running = 1
        self.loop()

    def loop(self):
        """The server's main loop"""
        while self.running:
            self.tick()
            time.sleep(1 / self.TICKS_PER_SECOND)

    def tick(self):
        """A single tick of a server. Reads the socket and treat the open ones."""
        read_list, write_list, _ = select.select([self.server_socket] + self.open_client_sockets,
                                                 self.open_client_sockets, [])
        for notified_socket in read_list:
            if notified_socket is self.server_socket:
                self.receive_connection()
            else:
                connected = self.handle_request(notified_socket)
                if not connected:
                    self.disconnect_user(User.users_list[notified_socket])

        self.send_waiting_messages(write_list)

    def receive_connection(self):
        """Receive a new connection"""
        client_socket, client_address = self.server_socket.accept()
        self.open_client_sockets.append(client_socket)
        User(client_socket, client_address)

    def handle_request(self, client_socket):
        """Handles one or more client requests. Splits it to command and arguments and calls the suitable function"""
        try:
            data = bytearray()
            while True:
                try:
                    new = client_socket.recv(4069)
                    if new:
                        data.extend(new)
                    else:
                        break
                except BlockingIOError:
                    break

            if not data:
                print("empty message...")
                return False

            requests = self.smart_split(data.decode(), '\n')
            for request in requests:
                command, kwargs = self.split_message(request)
                try:
                    self.commands[command](self, User.users_list[client_socket], **kwargs)
                except TypeError:
                    self.commands[command](self, User.users_list[client_socket], kwargs)
        except Exception as e:
            raise e
            return False
        return True

    def disconnect_user(self, user: User):
        """Safely disconnects a user from the server"""
        self.open_client_sockets.remove(user.socket)
        Message.remove_messages_to(user.socket)
        user.disconnect()

    @classmethod
    def command(cls, name=None):
        """Meant to be used as a decorator. Defines a new command."""
        if callable(name):  # called without parenthesis
            f = name
            cls.commands[f.__name__] = f
            return f

        def inner(f):
            cls.commands[name or f.__name__] = f
            return f

        return inner

    @staticmethod
    def send_waiting_messages(write_list):
        """Sends all the waiting messages that can be sent"""
        for message in Message.messages_to_send:
            if message.socket in write_list:
                message.send()

    @staticmethod
    def format_string(string):
        r"""Replaces %, & and = with \%, \& and \= respectively"""
        return str(string).replace('%', r'\%').replace('&', r'\&').replace('=', r'\=')

    @classmethod
    def build_packet(cls, command: str, **parameters):
        """Converts command and arguments to something that can be sent over a socket"""
        return cls.format_string(command).encode() + (b'?' if parameters else b'') + ('&'.join(
            ['{}={}'.format(cls.format_string(param), cls.format_string(val))
             for param, val in parameters.items()])).encode() + b'\n'

    @classmethod
    def split_message(cls, request: str):
        """Splits a message into command and arguments"""
        command, *arguments = cls.smart_split(request, '?')
        if arguments:
            args = [cls.smart_split(i, '=') for i in cls.smart_split(arguments[0], '&')]
            for arg in args:
                if len(arg) == 1:  # only argument but not value, assign default value.
                    arg.append('')
            kwargs = dict(args)
        else:
            kwargs = {}
        return command, kwargs

    @staticmethod
    def smart_split(string, separator, saver='\\'):
        """
        Split string by the separator, as long as saver is not present before it.
        for example: string='Hello0Dear0W\0rld, separator='0', saver='\' returns ['Hello', 'Dear', 'W0rld']
        """
        splited = string.split(separator)
        new_list = []
        i = 0
        while i < len(splited):
            item = splited[i]
            if item:
                if item[-1] == saver and not i + 1 == len(splited):  # merge it with the next item
                    item = item[:-1]
                    item += separator + splited[i + 1]
                    i += 1
                new_list.append(item)
            i += 1

        return new_list

    @staticmethod
    def encode_list(args):
        """Encodes a list to something that can be sent over a socket"""
        return ','.join(str(arg).replace(',', r'\,') for arg in args)

    @classmethod
    def decode_list(cls, lst):
        """Decodes the list encoded by encode_list"""
        return cls.smart_split(lst, ',')

    def send_message(self, socket_, command: str, **parameters):
        """Send a command and arguments to socket"""
        self.send_packet(socket_, self.build_packet(command, **parameters))

    @staticmethod
    def send_packet(socket_, packet):
        """Creates a message to be sent later"""
        Message(socket_, packet)

    def send_all(self, command: str, exceptions=(), *, user_exception=None, **parameters):
        """
        Send a message to all the users
        :param command: The command of the request
        :param exceptions: Users NOT to send the message to
        :param user_exception: a dict of this form:
            {user: {parameter: value, parameter2: value}, ...}
            This way one user can get a slightly different message than the others
        :param parameters:  The parameters of the request
        :return: The default packet (without the exceptions)
        """
        packet = self.build_packet(command, **parameters)
        for sock in self.open_client_sockets:
            if sock in exceptions:
                continue

            user = User.users_list[sock]
            Message(sock, packet if ((user_exception is None) or (user not in user_exception)) else
            self.build_packet(command, **self.merge_kwargs(user_exception, user, parameters)))
        return packet

    @staticmethod
    def merge_kwargs(user_exception, user, kwargs):
        """Merges the default arguments with the user_exception for a specific user"""
        if isinstance(user_exception, dict) and user in user_exception:
            return {**kwargs, **user_exception[user]}
        return kwargs


params = {}


def safe_kwargs(f):
    """
    Meant to be used as a decorator. Makes sure that if a command function only takes one argument, it will get it as a
    dictionary describing the keyword arguments it got.

    without it, a command defined as:

    @CommandClient.command
    def command(self, keyword_arguments):
        pass

    can get a request like "command?keyword_arguments=4". This is dangerous because the programmer really expected to
    get {"keyword_arguments": "4"} as keyword_arguments.
    """
    def inner(self, user, kwargs):
        if f not in params:
            params[f] = list(inspect.signature(f).parameters)[1]
        param_name = params[f]
        if not isinstance(kwargs, dict):
            kwargs = {param_name: kwargs}
        f(self, user, kwargs)

    inner.__name__ = f.__name__
    return inner


class GameClient:
    pass
