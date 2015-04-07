package org.elt.hazelcast_flow_table.hznode;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;

import org.ardverk.collection.PatriciaTrie;
import org.ardverk.collection.StringKeyAnalyzer;
import org.elt.hazelcast_flow_table.of.IP;
import org.elt.hazelcast_flow_table.of.MatchPart;
import org.elt.hazelcast_flow_table.of.OFPMatch;
import org.elt.hazelcast_flow_table.of.OFPFlowMod.OFPFC;
import org.elt.hazelcast_flow_table.proto.CompetitionErrorMessage;
import org.elt.hazelcast_flow_table.proto.FlowModMessage;
import org.elt.hazelcast_flow_table.proto.TableEntryTag;
import org.elt.hazelcast_flow_table.table.TableEntry;
import org.elt.hazelcast_flow_table.table.TableValue;

import com.hazelcast.query.Predicate;

public class IPIndexedFlowTable implements Serializable {

	private static final long serialVersionUID = 978805711164510034L;
	String dpid;
	
	PatriciaTrie<String, Set<Long>> srcTrie = new PatriciaTrie<String, Set<Long>>(StringKeyAnalyzer.BYTE);
	PatriciaTrie<String, Set<Long>> dstTrie = new PatriciaTrie<String, Set<Long>>(StringKeyAnalyzer.BYTE);
	Map<Long, TableEntry> table = new HashMap<Long, TableEntry>();
	Map<Long, String> nodeMap = new HashMap<Long, String>();
	long lastEntryId = 0;
	
	double totalPart = 0.0;
	int measures = 0;
	int[] cases = {0, 0, 0, 0};
	
	public IPIndexedFlowTable(String dpid) {
		this.dpid = dpid;
	}
	
	protected long getNextId() {
		return ++lastEntryId;
	}
	
	protected void updateTable(FlowModMessage msg, 
			Set<TableEntry> matches) {
		if (msg.getFlowMod().isAdd()) {
			// TODO: If pattern is the same, add works like modify.
			long id = getNextId();
			table.put(id, new TableEntry(id, msg.getMatchPart(), msg.getTableValue()));
			// Insert into trie.
			
			Set<Long> set;
			IP src = msg.getMatchPart().getMatch().getSrcIp();
			set = srcTrie.get(src.toBinaryString());
			if (set != null) {
				int size = set.size();
				set.add(id);
			} else {
				set = new HashSet<Long>();
				set.add(id);
				srcTrie.put(src.toBinaryString(), set);
			}
			
			IP dst = msg.getMatchPart().getMatch().getDstIp();
			set = dstTrie.get(dst.toBinaryString());
			if (set != null) {
				set.add(id);
			} else {
				set = new HashSet<Long>();
				set.add(id);
				dstTrie.put(dst.toBinaryString(), set);
			}
		} else if (msg.getFlowMod().isModify()) {
			if (matches.size() == 0) {
				byte command = msg.getFlowMod().getCommand();
				msg.getFlowMod().setCommand((byte)OFPFC.OFPFC_ADD.getValue());
				updateTable(msg, matches);
				msg.getFlowMod().setCommand(command);
			}
			for (TableEntry match: matches) {
				// TODO: How will we respond with original actions?
				TableEntry new_match = new TableEntry(match.getId(), match.getKey(), match.getValue().clone());
				TableValue v = new_match.getValue();
				TableEntryTag tag = v.getTag();
				tag.update(msg.getTag());
				v.setInstructionPart(msg.getFlowMod().getInstructionPart());
				// TODO: For non-distributed map, we do not need "put".
				table.put(new_match.getId(), new_match);
			}
		} else if (msg.getFlowMod().isDelete()) {
			for (TableEntry match: matches) {
				Set<Long> set = srcTrie.get(match.getKey().getMatch().getSrcIp().toBinaryString());
				if (set == null) {
					System.err.println("Evidently no set for src_ip " + 
								match.getKey().getMatch().getSrcIp().toString());
				} else {
					set.remove(match.getId());
				}
				set = dstTrie.get(match.getKey().getMatch().getDstIp().toBinaryString());
				if (set == null) {
					System.err.println("Evidently no set for dst_ip " + 
								match.getKey().getMatch().getDstIp().toString());
				} else {
					set.remove(match.getId());
				}
				table.remove(match.getId());
			}
		}
	}
	
	protected Set<Long> ipTrieLookup(FlowModMessage msg) {
		Set<Long> src_matches = new HashSet<Long>(), 
				  dst_matches = new HashSet<Long>(),
				  matchingIds;
		IP src = msg.getMatchPart().getMatch().getSrcIp();
		IP dst = msg.getMatchPart().getMatch().getDstIp();
		//System.err.println("Find " + src.toString() + " " + dst.toString());
		if (src.getMask() < 32) {
			for (Set<Long> set: srcTrie.prefixMap(src.toBinaryString()).values()) {
				src_matches.addAll(set);
			}
		}
		if (dst.getMask() < 32) {
			for (Set<Long> set: dstTrie.prefixMap(dst.toBinaryString()).values()) {
				dst_matches.addAll(set);
			}
		}
		if (src.getMask() < 32 && dst.getMask() < 32) {
			if (src_matches.size() < dst_matches.size()) {
				dst_matches.retainAll(src_matches);
				matchingIds = dst_matches;
			} else {
				src_matches.retainAll(dst_matches);
				matchingIds = src_matches;
			}
			cases[0]++;
		} else if (src.getMask() < 32) {
			matchingIds = src_matches;
			cases[1]++;
		} else if (dst.getMask() < 32) {
			matchingIds = dst_matches;
			cases[2]++;
		} else {
			matchingIds = table.keySet();
			cases[3]++;
		}
		
		if (table.size() > 0) {
			totalPart += 1.0 * matchingIds.size() / table.size();
			measures += 1;
		}
		return matchingIds;
	}
	
	protected Set<TableEntry> getEntriesById(FlowModMessage msg, Set<Long> matchingIds) {
		Predicate pred = PredicateCreator.createPredicate(msg);
		Set<TableEntry> matches = new HashSet<TableEntry>();
		TableEntry e;
		for (long id: matchingIds) {
			e = table.get(id);
			if (e == null) {
				System.err.println("No entry for key " + String.valueOf(id));
			}
			if (pred.apply(new QEntry(e))) {
				matches.add(e);
			}
		}
		return matches;
	}
	
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg) {
		// TODO: Maybe use Executor?	
		Set<Long> matchingIds = ipTrieLookup(msg);
		Set<TableEntry> matches = getEntriesById(msg, matchingIds);
		
		updateTable(msg, matches);
		// Switch by msg.command. Check for errors. Update map. Everything in locks =)
		return createMessage(msg, matches);
	}

	public void shutdown() {
		System.err.println("Stats: " + this.dpid);
		System.err.println("Average part: " + String.valueOf(totalPart/measures));
		System.err.println("Measures: " + String.valueOf(measures));
		System.err.println("Src and dst non-empty: " + String.valueOf(cases[0]));
		System.err.println("Src non-empty: " + String.valueOf(cases[1]));
		System.err.println("Dst non-empty: " + String.valueOf(cases[2]));
		System.err.println("Src and dst empty: " + String.valueOf(cases[3]));
	}
	
	protected int shortCompareUnsigned(short arg0, short arg1) {
		return Integer.compare(arg0 & 0xFFFF, arg1 & 0xFFFF);
	}
	
	protected CompetitionErrorMessage createMessage(FlowModMessage msg,
			Set<TableEntry> matches) {
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
				if (match.getKey().getMatch().equals(msgMatch)) {
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
