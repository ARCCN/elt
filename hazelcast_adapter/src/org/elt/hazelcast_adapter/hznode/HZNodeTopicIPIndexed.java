package org.elt.hazelcast_adapter.hznode;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.Queue;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

import org.elt.hazelcast_adapter.CompetitionErrorMessage;
import org.elt.hazelcast_adapter.FlowModMessage;
import org.elt.hazelcast_adapter.IFlowTable;

import com.hazelcast.core.Hazelcast;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.core.HazelcastInstanceAware;
import com.hazelcast.core.IMap;
import com.hazelcast.core.ITopic;
import com.hazelcast.core.IdGenerator;
import com.hazelcast.core.Message;
import com.hazelcast.core.MessageListener;
import com.hazelcast.core.ReplicatedMap;

public class HZNodeTopicIPIndexed implements IFlowTable, 
	MessageListener<FMMEvent> {

	HazelcastInstance instance;
	String name;
	long id;
	Lock tableLock = new ReentrantLock();
	Map<String, IPIndexedFlowTable> tables = new HashMap<String, IPIndexedFlowTable>();
	Map<String, Lock> locks = new HashMap<String, Lock>();
	IMap<Long, String> nodeMap;
	ReplicatedMap<String, Long> dpidToNode;
	IdGenerator gen;
	ITopic<CompetitionErrorMessage> replies;
	ITopic<FMMEvent> requests;
	Queue<CompetitionErrorMessage> replyQueue = new ConcurrentLinkedQueue<CompetitionErrorMessage>();
	// List<ITopic<FMMEvent>> requests = Collections.synchronizedList(new ArrayList<ITopic<FMMEvent>>());

	public class UpdateTask
	implements Callable<CompetitionErrorMessage>, Serializable, HazelcastInstanceAware
	{

		private static final long serialVersionUID = 2505663945800111489L;
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
	
	public class ReplyListener implements MessageListener<CompetitionErrorMessage> {
		
		private Queue<CompetitionErrorMessage> replyQueue;
		
		public ReplyListener(Queue<CompetitionErrorMessage> replyQueue) {
			this.replyQueue = replyQueue;
		}
		
		@Override
		public void onMessage(Message<CompetitionErrorMessage> arg0) {
			replyQueue.add(arg0.getMessageObject());
		}
	}
	
	public HZNodeTopicIPIndexed() {
		/*
		Config config = new Config();
		MapConfig mapConfig = new MapConfig();
		mapConfig.setName("tables");
		mapConfig.setBackupCount(0);
		mapConfig.setAsyncBackupCount(0);
		//mapConfig.setInMemoryFormat(InMemoryFormat.OBJECT);
		config.addMapConfig(mapConfig);
		*/
		this.instance = Hazelcast.newHazelcastInstance();
		this.gen = this.instance.getIdGenerator("gen");
		this.id = this.gen.newId();	
		this.name = this.instance.getCluster().getLocalMember().toString();
		//this.tables = this.instance.getMap("tables");
		this.nodeMap = this.instance.getMap("nodeMap");
		this.nodeMap.put(this.id, this.name);
		this.dpidToNode = this.instance.getReplicatedMap("dpidToNode");
		this.replies = this.instance.getTopic(String.valueOf(this.id) + "-reply");
		this.replies.addMessageListener(new ReplyListener(replyQueue));
		this.requests = this.instance.getTopic(String.valueOf(this.id) + "-request");
		this.requests.addMessageListener(this);
	}
	
	protected CompetitionErrorMessage runUpdateTask(String dpid, FlowModMessage msg) {
		Long node = dpidToNode.get(dpid);
		if (node == null) {
			// Take responsibility for this dpid.
			dpidToNode.put(dpid, id);
			node = id;
		}
		ITopic<FMMEvent> topic = this.instance.getTopic(
				String.valueOf(node) + "-request");
		topic.publish(new FMMEvent(msg, id));
		
		// Wait for response.
		// TODO: Async?
		while (this.replyQueue.isEmpty()) {
			try {
				Thread.sleep(1);
			} catch (InterruptedException e) {
			}
		}
		CompetitionErrorMessage error = this.replyQueue.poll();
		return error;
	}
	
	@Override
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg) {
		// TODO: Maybe use Executor?
		// TODO: MODIFY can act like ADD.
		// TODO: We may need several response messages,
		msg.setNode(this.id);
				
		String dpid = msg.getDpid();
		/*
		if (!tables.containsKey(dpid)) {
			tables.put(dpid, new IPIndexedFlowTable(dpid));
		}
		*/
		return runUpdateTask(dpid, msg);
	}

	@Override
	public void shutdown() {
		IPIndexedFlowTable table;
		tableLock.lock();
		for (String dpid: tables.keySet()) {
			table = tables.get(dpid);
			Lock lock = locks.get(dpid);
			lock.lock();
			table.shutdown();
			lock.unlock();
		}
		tableLock.unlock();
		this.instance.shutdown();
	}

	@Override
	public void onMessage(Message<FMMEvent> arg0) {
		// Process request.
		// TODO: Separate thread.
		FlowModMessage msg = arg0.getMessageObject().getMsg();
		String dpid = msg.getDpid();
		tableLock.lock();
		IPIndexedFlowTable table = tables.get(dpid);
		if (table == null) {
			table = new IPIndexedFlowTable(dpid);
			tables.put(dpid, table);
			locks.put(dpid, new ReentrantLock());
		}
		tableLock.unlock();
		Lock lock = locks.get(dpid);
		lock.lock();
	    CompetitionErrorMessage error = table.updateErrorChecking(msg);
	    lock.unlock();
	   
	    // Send reply.
	    ITopic<CompetitionErrorMessage> topic = this.instance.getTopic(String.valueOf(
	    		arg0.getMessageObject().getSource()) + "-reply");
	    topic.publish(error);
	}
}
