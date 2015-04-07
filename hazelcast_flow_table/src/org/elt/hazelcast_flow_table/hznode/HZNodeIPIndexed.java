package org.elt.hazelcast_flow_table.hznode;

import java.io.Serializable;
import java.util.concurrent.Callable;
import java.util.concurrent.locks.Lock;

import org.elt.hazelcast_flow_table.proto.CompetitionErrorMessage;
import org.elt.hazelcast_flow_table.proto.FlowModMessage;
import org.elt.hazelcast_flow_table.table.IFlowTable;

import com.hazelcast.config.Config;
import com.hazelcast.config.MapConfig;
import com.hazelcast.core.Hazelcast;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.core.HazelcastInstanceAware;
import com.hazelcast.core.IMap;
import com.hazelcast.core.IdGenerator;

public class HZNodeIPIndexed implements IFlowTable {

	HazelcastInstance instance;
	Lock tableLock;
	String name;
	long id;
	IMap<String, IPIndexedFlowTable> tables;
	IMap<Long, String> nodeMap;
	IdGenerator gen;

	public class UpdateTask
	    implements Callable<CompetitionErrorMessage>, Serializable, HazelcastInstanceAware {

		private static final long serialVersionUID = 4713143424725021783L;
		private transient HazelcastInstance hazelcastInstance;
		protected String dpid;
		protected FlowModMessage msg;
	
		public UpdateTask(String dpid, FlowModMessage msg) {
			this.dpid = dpid;
			this.msg = msg;
		}
		
		public void setHazelcastInstance( HazelcastInstance hazelcastInstance ) {
		    this.hazelcastInstance = hazelcastInstance;
		}
		
		public CompetitionErrorMessage call() {
		    IMap<String, IPIndexedFlowTable> tables = hazelcastInstance.getMap( "tables" );
		    tables.lock(dpid);
		    IPIndexedFlowTable table = tables.get(dpid);
		    CompetitionErrorMessage error = table.updateErrorChecking(msg);
		    tables.put(dpid, table);
		    tables.unlock(dpid);
		    return error;
		}
	}
	
	public HZNodeIPIndexed() {
		
		Config config = new Config();
		MapConfig mapConfig = new MapConfig();
		mapConfig.setName("tables");
		mapConfig.setBackupCount(0);
		mapConfig.setAsyncBackupCount(0);
		//mapConfig.setInMemoryFormat(InMemoryFormat.OBJECT);
		config.addMapConfig(mapConfig);
		
		this.instance = Hazelcast.newHazelcastInstance(config);
		this.gen = this.instance.getIdGenerator("gen");
		this.id = this.gen.newId();		
		this.tableLock = this.instance.getLock("tableLock");
		this.name = this.instance.getCluster().getLocalMember().toString();
		this.tables = this.instance.getMap("tables");
		this.nodeMap = this.instance.getMap("nodeMap");
		this.nodeMap.put(this.id, this.name);
	}
	
	protected CompetitionErrorMessage runUpdateTask(String dpid, FlowModMessage msg) {
		// Moved lock to Callable.
		//tables.lock(dpid);
		/*
		IExecutorService exec = instance.getExecutorService("default");
		Future<CompetitionErrorMessage> fut = exec.submitToKeyOwner(new UpdateTask(dpid, msg), dpid);
		CompetitionErrorMessage error = null;
		try {
			error = fut.get();
		}
		catch (Exception e) {}
		*/
		
		UpdateTask task = new UpdateTask(dpid, msg);
		task.setHazelcastInstance(instance);
		CompetitionErrorMessage error = task.call();
		
		//tables.unlock(dpid);
		return error;
	}
	
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
		return runUpdateTask(dpid, msg);
	}

	@Override
	public void shutdown() {
		IPIndexedFlowTable table;
		for (String dpid: tables.localKeySet()) {
			table = tables.get(dpid);
			table.shutdown();
		}
		this.instance.shutdown();
	}

}
