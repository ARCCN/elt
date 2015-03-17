package org.elt.hazelcast_adapter.hznode;

import java.util.HashMap;
import java.util.Map;

import org.elt.hazelcast_adapter.CompetitionErrorMessage;
import org.elt.hazelcast_adapter.FlowModMessage;
import org.elt.hazelcast_adapter.IFlowTable;

public class IPTrieNode implements IFlowTable {
	String name = "No name";
	long id = 0;
	
	Map<String, IPIndexedFlowTable> tables = new HashMap<String, IPIndexedFlowTable>();
	
	@Override
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg) {
		// TODO: Maybe use Executor?
		// TODO: MODIFY can act like ADD.
		// TODO: We may need several response messages,
		msg.setNode(this.id);
		
		String dpid = msg.getDpid();
		if (!tables.containsKey(dpid)) {
			tables.put(dpid, new IPIndexedFlowTable(dpid));
		}
		return tables.get(dpid).updateErrorChecking(msg);
	}

	@Override
	public void shutdown() {
		for (IPIndexedFlowTable table: tables.values()) {
			table.shutdown();
		}
	}

}
