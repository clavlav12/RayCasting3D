from threading import Thread
import socket
import select
import inspect


class MetaClient(type):
    def __new__(mcs, name, bases, attrs):
        """Makes sure commands are inherited"""
        cls = type.__new__(mcs, name, bases, attrs)
        if 'commands' in attrs:
            dictionary = attrs['commands']
            if not isinstance(dictionary, dict):
                raise AttributeError('"commands" attribute must be of type "dict"')
            for base in cls.__bases__:
                try:
                    if issubclass(base, CommandClient):
                        print(cls.commands, base.commands)
                        cls.commands = {**cls.commands, **base.commands}  # inheriting the commands
                except NameError: # CommandServer is not yet maid
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


class CommandClient(Thread, metaclass=MetaClient):
    SERVER_PORT = 35241
    IP = "127.0.0.1"
    commands = {}

    def __init__(self):
        super(CommandClient, self).__init__()
        self.socket = None

    def run(self):
        """Runs the client"""
        self.connected = self.connect_server()
        while self.connected:
            read_list = select.select([self.socket], [], [], 1)[0]
            if read_list:
                self.handle_request()
        self.socket.close()

    def connect_server(self):
        """Connects to the server"""
        self.socket = socket.socket()
        self.socket.settimeout(10)
        try:
            ip = self.IP
            self.socket.connect((ip, self.SERVER_PORT))
            self.connect()
            self.socket.setblocking(False)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return True
        except (Exception, socket.timeout) as e:
            raise e
            return False

    def disconnect_and_quit(self):
        """Safely disconnects from the server"""
        try:
            self.socket.send(self.build_packet('Disconnect'))
            self.connected = False
        except Exception as e:
            print(e)
            pass

    def handle_request(self):
        """Handles one or more server requests. Splits it to command and arguments and calls the suitable function"""
        try:
            data = bytearray()
            while True:
                try:
                    new = self.socket.recv(4069)
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
                    self.commands[command](self, **kwargs)
                except TypeError:
                    self.commands[command](self, kwargs)

        except Exception as e:
            raise e
            # warnings.warn("Something broken\n " + repr(e))
            return False
        return True

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
            a = [cls.smart_split(i, '=') for i in cls.smart_split(arguments[0], '&')]
            kwargs = dict(a)
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
                if item[-1] == saver and not i+1 == len(splited):  # merge it with the next item
                    item = item[:-1]
                    item += separator + splited[i+1]
                    i += 1
                new_list.append(item)
            i += 1

        return new_list

    @staticmethod
    def encode_list(args):
        """Encodes a list to something that can be sent over a socket"""
        return ','.join(arg.replace(',', r'\,') for arg in args)

    @classmethod
    def decode_list(cls, lst):
        """Decodes the list encoded by encode_list"""
        return cls.smart_split(lst, ',')

    def send_message(self, command: str, **parameters):
        """Send a command and arguments to the server"""
        self.socket.send(self.build_packet(command, **parameters))

    def connect(self):
        """Called after the three-way-handshake. Sends a protocol-valid connect request to the server."""
        print("sent connect")
        self.send_message('Connect')


class FalseDict(dict):
    """
    Dictionary that returns false instead of raising KeyError if key is not found
    """

    def __getitem__(self, item):
        try:
            return super(FalseDict, self).__getitem__(item)
        except KeyError:
            return False


class OtherUser:
    """User whose active keys are always nothing"""
    def __init__(self):
        self.active_keys = FalseDict()

    def __bool__(self):
        return False


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
    def inner(self, kwargs):
        if f not in params:
            params[f] = list(inspect.signature(f).parameters)[1]
        param_name = params[f]
        if not isinstance(kwargs, dict):
            kwargs = {param_name: kwargs}
        f(self, kwargs)
    return inner


    class GameClient:
        pass
