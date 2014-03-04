import MySQLdb as mdb
import sys
import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of
import time

class Database:

  SIMPLE = 0
  DICTIONARY = 1

  def __init__(self):
    self.connect()
    self.create_tables()
    

  def connect(self):
    try:
      self.con = mdb.connect('localhost', 'user', 
        '1234', 'Traffic')
    except:
      pass
        
  def create_tables(self):
    if self.con:
      cur = self.con.cursor()
      cur.execute("CREATE TABLE IF NOT EXISTS FlowMatch( \
           ID INT UNSIGNED PRIMARY KEY AUTO_INCREMENT, \
           dl_src BIGINT UNSIGNED, \
           dl_dst BIGINT UNSIGNED, \
           dl_vlan SMALLINT UNSIGNED, \
           dl_vlan_pcp TINYINT UNSIGNED, \
           dl_type SMALLINT UNSIGNED, \
           nw_tos TINYINT UNSIGNED, \
           nw_proto TINYINT UNSIGNED, \
           nw_src INT UNSIGNED, \
           nw_dst INT UNSIGNED, \
           tp_src SMALLINT UNSIGNED, \
           tp_dst SMALLINT UNSIGNED \
           )")
      cur.execute("CREATE TABLE IF NOT EXISTS FlowHistory( \
           ID INT UNSIGNED, \
           time DATETIME, \
           dpid BIGINT, \
           in_port SMALLINT UNSIGNED, \
           src_dpid BIGINT, \
           src_port SMALLINT UNSIGNED \
           )")
      
  def disconnect(self):
    if self.con: 
      self.con.close()
      
  def clear(self):
    if self.con:
      cur = self.con.cursor()
      cur.execute("DELETE FROM FlowMatch")
      cur.execute("DELETE FROM FlowHistory")
      
  def add_flow(self, packet):
    if self.con:
      match = of.ofp_match.from_packet(packet)
      cur = self.con.cursor()
      query = "INSERT INTO FlowMatch(dl_src, dl_dst, dl_vlan, dl_vlan_pcp, \
            dl_type, nw_tos, nw_proto, nw_src, nw_dst, tp_src, tp_dst) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % \
            (match.dl_src.toInt(), match.dl_dst.toInt(), match.dl_vlan, \
	    match.dl_vlan_pcp, match.dl_type, match.nw_tos, match.nw_proto, \
	    match.nw_src.toUnsigned() if match.nw_src else match.nw_src, \
            match.nw_dst.toUnsigned() if match.nw_dst else match.nw_dst, \
            match.tp_src, match.tp_dst)
      query = query.replace("None", "NULL")
      #print(query)
      cur.execute(query)
      
  def add_history(self, packet, dpid, in_port, src_dpid = None, src_port = None, t = None):
    if self.con:
      
      match = of.ofp_match.from_packet(packet)
      cur = self.con.cursor()
      query = "SELECT ID FROM FlowMatch WHERE dl_src = %s AND dl_dst = %s AND \
       dl_vlan = %s AND dl_vlan_pcp = %s AND dl_type = %s AND nw_tos = %s AND nw_proto = %s AND\
       nw_src = %s AND nw_dst = %s AND tp_src = %s AND tp_dst = %s" % \
       (match.dl_src.toInt(), match.dl_dst.toInt(), match.dl_vlan, match.dl_vlan_pcp, match.dl_type, \
       match.nw_tos, match.nw_proto, match.nw_src.toUnsigned() if match.nw_src else match.nw_src, \
       match.nw_dst.toUnsigned() if match.nw_dst else match.nw_dst, match.tp_src, \
       match.tp_dst)
      query = query.replace("= None", " IS NULL")
      #print(query)
      cur.execute(query)
      id = cur.fetchone()
      if id is None:
        self.add_flow(packet)
        cur.execute(query)
        id = cur.fetchone()
        if id is None:
          print("DB ERROR: Unable to add flow")
      if t is None:
        t = time.gmtime()
      query = "INSERT INTO FlowHistory(ID, time, dpid, in_port, src_dpid, \
              src_port) VALUES (%d, \"%s\", %d, %d, %s, %s )" \
              % (int(id[0]), time.strftime("%Y-%m-%d %H:%M:%S", t), \
                dpid, in_port, str(src_dpid), str(src_port))
      query = query.replace("None", "NULL")
      #print(query)
      cur.execute(query)

  def execute_query(self, query, cursor = None):
    if self.con:
      cur = None
      if cursor is None or cursor == self.SIMPLE:
        cur = self.con.cursor()
      elif cursor == self.DICTIONARY:
        cur = self.con.cursor(mdb.cursors.DictCursor)
      if cur is None:
        return None
      cur.execute(query)
      rows = cur.fetchall()
      return rows
      
