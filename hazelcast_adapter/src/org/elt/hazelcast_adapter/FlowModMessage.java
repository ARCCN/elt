package org.elt.hazelcast_adapter;

import java.lang.reflect.Constructor;
import java.util.HashMap;
import java.util.Map;

import org.elt.hazelcast_adapter.hznode.TableEntry;
import org.elt.hazelcast_adapter.hznode.TableValue;
import org.elt.hazelcast_adapter.of.InstructionPart;
import org.elt.hazelcast_adapter.of.MatchPart;
import org.elt.hazelcast_adapter.of.OFPFlowMod;
import org.elt.hazelcast_adapter.of.OFPMatch;
import org.elt.hazelcast_adapter.of.OFPRule;
import org.elt.hazelcast_adapter.of.OFPFlowMod.OFPFC;
import org.elt.hazelcast_adapter.unpack.FlowModFactory;
import org.elt.hazelcast_adapter.unpack.IDumpable;
import org.elt.hazelcast_adapter.unpack.ILoadable;

public class FlowModMessage implements ILoadable, IDumpable {
	OFPFlowMod flow_mod;
	String dpid;
	TableEntryTag tag;
	
	public FlowModMessage() {
	}
	
	public FlowModMessage(OFPFlowMod flow_mod) {
		this.flow_mod = flow_mod;
	}
	
	public FlowModMessage(OFPFlowMod flow_mod, String dpid, TableEntryTag tag) {
		this.flow_mod = flow_mod;
		this.dpid = dpid;
		this.tag = tag;
	}
	
	public void setNode(long node) {
		this.tag.addNode(node);
	}

	@Override
	public void fromJSON(Map map) throws Exception {
		String _name = (String)map.get("_name");
		if (!_name.equals("FlowModMessage"))
			throw new Exception();
		this.flow_mod = FlowModFactory.create((Map)map.get("flow_mod"));
		this.dpid = (String)map.get("dpid");
		this.tag = new TableEntryTag();
		this.tag.fromJSON((Map)map.get("tag"));
	}
	
	public MatchPart getMatchPart() { 
		MatchPart mp = this.flow_mod.toMatchPart();
		mp.setDpid(this.dpid);
		return mp;
	}
	
	public static FlowModMessage fromTable(MatchPart mp, 
			InstructionPart ip, TableEntryTag tag) {
		try {
			Class<? extends OFPFlowMod> c = FlowModFactory.getClass(mp.getVersion());
			Constructor cons = c.getConstructor(short.class, byte.class, 
					OFPMatch.class, InstructionPart.class);
			OFPFlowMod ofm = (OFPFlowMod)cons.newInstance(mp.getPriority(), 
					OFPFC.OFPFC_ADD.getValue(), mp.getMatch(), ip);
			FlowModMessage fm = new FlowModMessage(ofm, mp.getDpid(), tag);
			return fm;
		}
		catch (Exception e) { return null; }
	}
	
	public TableValue getTableValue() {
		return new TableValue(this.flow_mod.getInstructionPart(), this.tag);
	}
	/*
	public TableEntry toTableEntry() {
		try {
			OFPRule rule = this.flow_mod.toRule();
			return new TableEntry(rule, this.tag);
		}
		catch (Exception e) { return null; }
	}
	*/
	public OFPFlowMod getFlowMod() { return this.flow_mod; }
	public TableEntryTag getTag() { return this.tag; }

	@Override
	public Map<String, Object> dump() throws Exception {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("flow_mod", this.flow_mod.dump());
		map.put("dpid", this.dpid);
		map.put("tag", this.tag.dump());
		return map;
	}
}
