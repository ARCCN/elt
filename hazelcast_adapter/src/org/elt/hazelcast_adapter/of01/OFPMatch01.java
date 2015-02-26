package org.elt.hazelcast_adapter.of01;

import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.elt.hazelcast_adapter.of.OFPMatch;

public class OFPMatch01 extends OFPMatch {
	final static String[] names = {"wildcards", "in_port", "dl_src", "dl_dst", 
			  "dl_vlan", "dl_vlan_pcp", "dl_type", "nw_tos", 
			  "nw_proto", "nw_src", "nw_dst", "tp_src", "tp_dst"};
//	int wildcards; /* Wildcard fields. */
//	short in_port; /* Input switch port. */
//	String dl_src; /* Ethernet source address. */
//	String dl_dst; /* Ethernet destination address. */
//	short dl_vlan; /* Input VLAN id. */
//	byte dl_vlan_pcp; /* Input VLAN priority. */
//	short dl_type; /* Ethernet frame type. */
//	byte nw_tos; /* IP ToS (actually DSCP field, 6 bits). */
//	byte nw_proto; /* IP protocol or lower 8 bits of ARP opcode. */
//	int nw_src; /* IP source address. */
//	int nw_dst; /* IP destination address. */
//	short tp_src; /* TCP/UDP source port. */
//	short tp_dst; /* TCP/UDP destination port. */
	private final static long serialVersionUID = 0x1000000;
	
	int wildcards; /* Wildcard fields. */
	int in_port; /* Input switch port. */
	String dl_src; /* Ethernet source address. */
	String dl_dst; /* Ethernet destination address. */
	int dl_vlan; /* Input VLAN id. */
	int dl_vlan_pcp; /* Input VLAN priority. */
	int dl_type; /* Ethernet frame type. */
	int nw_tos; /* IP ToS (actually DSCP field, 6 bits). */
	int nw_proto; /* IP protocol or lower 8 bits of ARP opcode. */
	int nw_src; /* IP source address. */
	int nw_dst; /* IP destination address. */
	int tp_src; /* TCP/UDP source port. */
	int tp_dst; /* TCP/UDP destination port. */
	
	public OFPMatch01() {	
	}
	
	public Set<String> getUnmasked() {
		Set<String> result = new HashSet<String>();
		// Mask shifts. -1 if not applicable or not 1 bit in mask.
		int[] shifts = {-1, 0, 2, 3, 1, 20, 4, 21, 5, -1, -1, 6, 7};
		for (int i=0; i < names.length; ++i) {
			if (shifts[i] != -1 && (((this.wildcards >> shifts[i]) & 1) == 0))
				result.add(names[i]);
		}
		int nw_src_mask = (this.wildcards >> 8) & ((1 << 6) - 1);
		int nw_dst_mask = (this.wildcards >> 14) & ((1 << 6) - 1);
		
		if (nw_src_mask < 32)
			result.add("nw_src");
		if (nw_dst_mask < 32)
			result.add("nw_dst");
		
		return result;
	}
	
	public OFPMatch01(int wildcards, short in_port, String dl_src, String dl_dst, 
				short dl_vlan, byte dl_vlan_pcp, short dl_type, byte nw_tos, 
				byte nw_proto, int nw_src, int nw_dst, short tp_src, short tp_dst) {
		this.wildcards = wildcards;
		this.in_port = in_port;
		this.dl_src = dl_src;
		this.dl_dst = dl_dst;
		this.dl_vlan = dl_vlan;
		this.dl_vlan_pcp = dl_vlan_pcp;
		this.dl_type = dl_type;
		this.nw_tos = nw_tos;
		this.nw_proto = nw_proto;
		this.nw_src = nw_src;
		this.nw_dst = nw_dst;
		this.tp_src = tp_src;
		this.tp_dst = tp_dst;
	}

	@Override
	public void fromJSON(Map<String, Object> map) throws Exception {
		//String[] names = {"wildcards", "in_port", "dl_src", "dl_dst", 
		//				  "dl_vlan", "dl_vlan_pcp", "dl_type", "nw_tos", 
		//				  "nw_proto", "nw_src", "nw_dst", "tp_src", "tp_dst"};
		//Object[] obs = {this.wildcards, this.in_port, this.dl_src, this.dl_dst, 
		//				this.dl_vlan, this.dl_vlan_pcp, this.dl_type, this.nw_tos, 
		//				this.nw_proto, this.nw_src, this.nw_dst, this.tp_src, this.tp_dst};
		
		Class <?> c = OFPMatch01.class;
		for (int i = 0; i < names.length; ++i) {
			Field f = c.getDeclaredField(names[i]);
			Object o = (Object)map.get(names[i]);
			if (o == null)
				continue;
			String value = o.toString();
			if (f.getType() == String.class)
				f.set(this, value);
			else {
				f.set(this, Integer.parseInt( value ) );
			}
		}
		/*
		this.wildcards = Integer.parseInt((String)map.get("wildcards"));
		this.in_port = (short)Integer.parseInt((String)map.get("in_port"));
		this.dl_src = (String)map.get("dl_src");
		this.dl_dst = (String)map.get("dl_dst");
		this.dl_vlan = (short)Integer.parseInt((String)map.get("dl_vlan"));
		this.dl_vlan_pcp = (byte)Integer.parseInt((String)map.get("dl_vlan_pcp"));
		this.dl_type = (short)Integer.parseInt((String)map.get("dl_type"));
		this.nw_tos = (byte)Integer.parseInt((String)map.get("nw_tos"));
		this.nw_proto = (byte)Integer.parseInt((String)map.get("nw_proto"));
		this.nw_src = Integer.parseInt((String)map.get("nw_src"));
		this.nw_dst = Integer.parseInt((String)map.get("nw_dst"));
		this.tp_src = (short)Integer.parseInt((String)map.get("tp_src"));
		this.tp_dst = (short)Integer.parseInt((String)map.get("tp_dst"));
		*/
	}

	@Override
	public int compareTo(Object o) {
		if (!(o instanceof OFPMatch01)) {
			assert false;
			return -1;
		}
		OFPMatch01 m = (OFPMatch01)o;
		Set<String> umsk = this.getUnmasked(), mUmsk = m.getUnmasked();
		boolean equalUmsk = umsk.equals(mUmsk);
		Class <?> c = OFPMatch01.class;
		Field f;
		for (String name: umsk) {
			if (!mUmsk.contains(name))
				continue;
			try {
				f = c.getDeclaredField(name);
				if (name.equals("nw_src")) {
					int nw_src_mask_1 = (this.wildcards >> 8) & ((1 << 6) - 1);
					int nw_src_mask_2 = (m.wildcards >> 8) & ((1 << 6) - 1);
					int mask = Math.max(nw_src_mask_1, nw_src_mask_2);
					if ((this.nw_src & ~((1 << mask) - 1)) != (m.nw_src & ~((1 << mask) - 1)))
						return -1;
				} else if (name.equals("nw_dst")) {
					int nw_dst_mask_1 = (this.wildcards >> 14) & ((1 << 6) - 1);
					int nw_dst_mask_2 = (m.wildcards >> 14) & ((1 << 6) - 1);
					int mask = Math.max(nw_dst_mask_1, nw_dst_mask_2);
					if ((this.nw_dst & ~((1 << mask) - 1)) != (m.nw_dst & ~((1 << mask) - 1)))
						return -1;
				} else {
					if (f.get(umsk) != f.get(mUmsk)) {
						return -1;
					}
				}
				
			} catch (Exception e) {
				continue;
			}
		}
		if (equalUmsk)
			return 0;
		else
			return 1;
	}
	/*
	@Override
	public int widerThan(OFPMatch o) {
		if (!(o instanceof OFPMatch01)) {
			assert false;
			return 0;
		}
		OFPMatch01 m = (OFPMatch01)o;
		Set<String> umsk = this.getUnmasked(), mUmsk = m.getUnmasked();
		boolean equalUmsk = umsk.equals(mUmsk);
		Class <?> c = OFPMatch01.class;
		Field f;
		for (String name: umsk) {
			if (!mUmsk.contains(name))
				continue;
			try {
				f = c.getDeclaredField(name);
				if (name.equals("nw_src")) {
					int nw_src_mask_1 = (this.wildcards >> 8) & ((1 << 6) - 1);
					int nw_src_mask_2 = (m.wildcards >> 8) & ((1 << 6) - 1);
					int mask = Math.max(nw_src_mask_1, nw_src_mask_2);
					if ((this.nw_src & ~((1 << mask) - 1)) != (m.nw_src & ~((1 << mask) - 1)))
						return -1;
				} else if (name.equals("nw_dst")) {
					int nw_dst_mask_1 = (this.wildcards >> 14) & ((1 << 6) - 1);
					int nw_dst_mask_2 = (m.wildcards >> 14) & ((1 << 6) - 1);
					int mask = Math.max(nw_dst_mask_1, nw_dst_mask_2);
					if ((this.nw_dst & ~((1 << mask) - 1)) != (m.nw_dst & ~((1 << mask) - 1)))
						return -1;
				} else {
					if (f.get(umsk) != f.get(mUmsk)) {
						return -1;
					}
				}
				
			} catch (Exception e) {
				continue;
			}
		}
	}
	*/
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		Class <?> c = OFPMatch01.class;
		try {
			Set<String> umsk = getUnmasked();
			for (int i = 0; i < names.length; ++i) {
				Field f = c.getDeclaredField(names[i]);
				if (f.getType() == String.class)
					map.put(names[i], f.get(this));
				else {
					int mask = 0xFFFFFFFF;
					if (f.getType() == byte.class)
						mask = 0xFF;
					else if (f.getType() == short.class)
						mask = 0xFFFF;
					if (names[i].equals("wildcards") || umsk.contains(names[i])) {
						map.put(names[i], ((int)f.get(this)) & mask);
					} else {
						map.put(names[i], null);
					}
				}
			}
		}
		catch (NoSuchFieldException | IllegalAccessException e) {} 
		return map;
	}
}
