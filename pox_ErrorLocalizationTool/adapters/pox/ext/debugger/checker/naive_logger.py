class Log():
  def __init__(self):
    self.debug_file = file("debug.log", "w")
    self.info_file = file("info.log", "w")
    self.print_buffer = ''

  def debug(self, string):
    #print "DEBUG: " + string
    self.debug_file.write("DEBUG: " + string + "\n")
    #self.f.flush()
    pass
    
  def error(self, string):
    print "ERROR: " + string
    
  def info(self, string):
    #print "INFO: " + string
    self.info_file.write("INFO: " + string + "\n")
    self.debug_file.write("DEBUG: " + string + "\n")

    #self.f.flush()
    pass

  def warning(self, string):
    print "WARNING: " + string

  def flush(self):
    self.debug_file.flush()
    self.info_file.flush()

  def raw(self, string):
    self.debug_file.write(string)

  def print_store(self, string):
    self.print_buffer += string + '\n'
 
  def print_flush(self):
    print(self.print_buffer)
    self.print_clear()

  def print_clear(self):
    self.print_buffer = ''
    
log = Log()

