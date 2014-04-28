class LoggingCursor(object):
    def __init__(self, cur, log_file):
        self.cur = cur
        self.log_file = log_file

    def __getattr__(self, name):
        if name == "cur":
            return self.cur
        if name == "execute":
            return self.execute
        else:
            return getattr(self.cur, name)

    def __setattr__(self, name, value):
        if name == "cur":
            self.__dict__[name] = value
        elif name == "execute":
            self.__dict__[name] = value
        else:
            return setattr(self.cur, name, value)

    def execute(self, query, args=None):
        s = str(query)
        if s[-1] == ';':
            self.log_file.write(s + "\n")
        else:
            self.log_file.write(s + ";\n")
        return self.cur.execute(query, args)


class LoggingConnection(object):
    def __init__(self, con, log_file):
        self.con = con
        self.log_file = log_file

    def cursor(self):
        return LoggingCursor(self.con.cursor(), self.log_file)

    def close(self):
        self.con.close()
