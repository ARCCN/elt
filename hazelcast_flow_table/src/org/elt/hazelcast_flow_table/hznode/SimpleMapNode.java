package org.elt.hazelcast_flow_table.hznode;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

import org.elt.hazelcast_flow_table.of.MatchPart;
import org.elt.hazelcast_flow_table.of.OFPFlowMod.OFPFC;
import org.elt.hazelcast_flow_table.of.OFPMatch;
import org.elt.hazelcast_flow_table.proto.CompetitionErrorMessage;
import org.elt.hazelcast_flow_table.proto.FlowModMessage;
import org.elt.hazelcast_flow_table.proto.TableEntryTag;
import org.elt.hazelcast_flow_table.table.IFlowTable;
import org.elt.hazelcast_flow_table.table.TableValue;

import com.hazelcast.query.Predicate;

public class SimpleMapNode implements IFlowTable {
	String name;
	long id;
	Map<MatchPart, TableValue> table;
	Map<Long, String> nodeMap;
	
	public SimpleMapNode() {
		this.name = "Single";
		this.table = new HashMap<MatchPart, TableValue>();
		this.nodeMap = new HashMap<Long, String>();
		this.id = 0;
		this.nodeMap.put(this.id, this.name);
	}
	
	public void shutdown() {
	}

	protected void updateTable(FlowModMessage msg, 
			Set<Entry<MatchPart, TableValue>> matches) {
		if (msg.getFlowMod().isAdd()) {
			table.put(msg.getMatchPart(), msg.getTableValue());
		} else if (msg.getFlowMod().isModify()) {
			if (matches.size() == 0) {
				byte command = msg.getFlowMod().getCommand();
				msg.getFlowMod().setCommand((byte)OFPFC.OFPFC_ADD.getValue());
				updateTable(msg, matches);
				msg.getFlowMod().setCommand(command);
			}
			for (Entry<MatchPart, TableValue> match: matches) {
				TableValue v = match.getValue();
				TableEntryTag tag = v.getTag();
				tag.update(msg.getTag());
				v.setInstructionPart(msg.getFlowMod().getInstructionPart());
				table.put(match.getKey(), v);
			}
		} else if (msg.getFlowMod().isDelete()) {
			for (Entry<MatchPart, TableValue> match: matches) {
				table.remove(match.getKey());
			}
		}
	}
	
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg) {
		msg.setNode(this.id);
		Predicate pred = PredicateCreator.createPredicate(msg);
		Set<Entry<MatchPart, TableValue>> total = table.entrySet();
		Set<Entry<MatchPart, TableValue>> matches = new HashSet<Entry<MatchPart, TableValue>>();
		for (Entry<MatchPart, TableValue> e: total) {
			if (pred.apply(new QEntry(e))) {
				matches.add(e);
			}
		}
		updateTable(msg, matches);
		return createMessage(msg, matches);
	}

	protected int shortCompareUnsigned(short arg0, short arg1) {
		return Integer.compare(arg0 & 0xFFFF, arg1 & 0xFFFF);
	}
	
	protected CompetitionErrorMessage createMessage(FlowModMessage msg,
			Set<Entry<MatchPart, TableValue>> matches) {
		ArrayList<FlowModMessage> masked = new ArrayList<FlowModMessage>();
		ArrayList<FlowModMessage> modified = new ArrayList<FlowModMessage>();
		ArrayList<FlowModMessage> undefined = new ArrayList<FlowModMessage>();
		ArrayList<FlowModMessage> deleted = new ArrayList<FlowModMessage>();
		
		CompetitionErrorMessage cmsg = new CompetitionErrorMessage();
		
		OFPMatch msgMatch = msg.getFlowMod().getMatch();
		for (Entry<MatchPart, TableValue> match: matches) {
			
			if (msg.getFlowMod().isDelete()) {
				deleted.add(FlowModMessage.fromMatch(match));
			} else if (msg.getFlowMod().isModify()) {
				modified.add(FlowModMessage.fromMatch(match));
			} else if (msg.getFlowMod().isAdd()) {
				if (match.getKey().getMatch().compareTo(msgMatch) == 0) {
					modified.add(FlowModMessage.fromMatch(match));
				} else if (match.getKey().getPriority() == msg.getFlowMod().getPriority()){
					undefined.add(FlowModMessage.fromMatch(match));
				} else if (shortCompareUnsigned(
						match.getKey().getPriority(), msg.getFlowMod().getPriority()) < 0) {
					masked.add(FlowModMessage.fromMatch(match));
				} else if (shortCompareUnsigned(
						match.getKey().getPriority(), msg.getFlowMod().getPriority()) > 0) {
					// TODO: Newly installed rule is masked.
					cmsg.addError("FlowMasked", FlowModMessage.fromMatch(match), 
							Arrays.asList(msg).toArray(new FlowModMessage[1]));
				} else assert false;
			} else {
				assert false;
			}
		}
		if (masked.size() > 0) {
			cmsg.addError("FlowMasked", msg, masked.toArray(new FlowModMessage[masked.size()]));
		}
		if (modified.size() > 0) {
			cmsg.addError("FlowModified", msg, modified.toArray(new FlowModMessage[modified.size()]));
		}
		if (undefined.size() > 0) {
			cmsg.addError("FlowUndefined", msg, undefined.toArray(new FlowModMessage[undefined.size()]));
		}
		if (deleted.size() > 0) {
			cmsg.addError("FlowDeleted", msg, deleted.toArray(new FlowModMessage[deleted.size()]));
		}
		
		return cmsg;
	}

}
