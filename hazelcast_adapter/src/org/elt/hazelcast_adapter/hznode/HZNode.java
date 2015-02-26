package org.elt.hazelcast_adapter.hznode;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Map.Entry;
import java.util.Set;
import java.util.concurrent.Future;
import java.util.concurrent.locks.Lock;

import org.elt.hazelcast_adapter.CompetitionErrorMessage;
import org.elt.hazelcast_adapter.FlowModMessage;
import org.elt.hazelcast_adapter.TableEntryTag;
import org.elt.hazelcast_adapter.of.MatchPart;
import org.elt.hazelcast_adapter.of.OFPMatch;

import com.hazelcast.core.Hazelcast;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.core.IMap;
import com.hazelcast.core.IdGenerator;
import com.hazelcast.query.Predicate;

public class HZNode {
	HazelcastInstance instance;
	Lock tableLock;
	String name;
	long id;
	IMap<MatchPart, TableValue> table;
	IMap<Long, String> nodeMap;
	IdGenerator gen;
	
	public HZNode() {
		this.instance = Hazelcast.newHazelcastInstance();
		this.tableLock = this.instance.getLock("tableLock");
		this.name = this.instance.getCluster().getLocalMember().toString();
		this.table = this.instance.getMap("table");
		this.nodeMap = this.instance.getMap("nodeMap");
		this.gen = this.instance.getIdGenerator("gen");
		this.id = this.gen.newId();
		this.nodeMap.put(this.id, this.name);
	}
	
	public void shutdown() {
		this.instance.shutdown();
	}

	protected void updateTable(FlowModMessage msg, 
			Set<Entry<MatchPart, TableValue>> matches) {
		// TODO: This is not Node's job. Need refactoring.
		if (msg.getFlowMod().isAdd()) {
			table.put(msg.getMatchPart(), msg.getTableValue());
		} else if (msg.getFlowMod().isModify()) {
			for (Entry<MatchPart, TableValue> match: matches) {
				TableValue v = match.getValue();
				TableEntryTag tag = v.getTag();
				tag.update(msg.getTag());
				v.setInstructionPart(msg.getFlowMod().getInstructionPart());
				table.set(match.getKey(), v);
			}
		} else if (msg.getFlowMod().isDelete()) {
			List<Future<TableValue>> futures = new LinkedList<Future<TableValue>>();
			for (Entry<MatchPart, TableValue> match: matches) {
				futures.add(table.removeAsync(match.getKey()));
			}
			for (Future<TableValue> f: futures) {
				try {
					while ( !f.isDone() ) 
						Thread.sleep(0, 1000);
				}
				catch (Exception e) {}
			}
		}
	}
	
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg) {
		// TODO: Maybe use Executor?
		// TODO: MODIFY can act like ADD.
		// TODO: We may need several response messages,
		msg.setNode(this.id);
		Predicate pred = PredicateCreator.createPredicate(msg);
		tableLock.lock();
		Set<Entry<MatchPart, TableValue>> matches = table.entrySet(pred);
		//int size = matches.size();
		updateTable(msg, matches);
		// TODO: Switch by msg.command. Check for errors. Update map. Everything in locks =)
		tableLock.unlock();
		return createMessage(msg, matches);
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
				} else if (match.getKey().getPriority() < msg.getFlowMod().getPriority()) {
					masked.add(FlowModMessage.fromMatch(match));
				} else if (match.getKey().getPriority() > msg.getFlowMod().getPriority()) {
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
