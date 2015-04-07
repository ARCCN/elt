package org.elt.hazelcast_flow_table.hznode;

import java.lang.reflect.Method;
import java.util.Map;

import com.hazelcast.nio.serialization.Data;
import com.hazelcast.query.QueryException;
import com.hazelcast.query.impl.AttributeType;
import com.hazelcast.query.impl.QueryableEntry;

class QEntry implements QueryableEntry {

	private Map.Entry entry;
	
	public QEntry(Map.Entry e) {
		assert e != null;
		entry = e;
	}
	
	@Override
	public Object setValue(Object value) {
		assert value != null;
		Object old = entry.getValue();
		entry.setValue(value);
		return old;
	}

	@Override
	public Data getIndexKey() {
		return null;
	}

	@Override
	public Data getKeyData() {
		return null;
	}

	@Override
	public Data getValueData() {
		return null;
	}

	@Override
	public Comparable getAttribute(String arg0) throws QueryException {
		// TODO Auto-generated method stub
		try {
			if (arg0 == null) {
				System.err.println("GetAttribute name = null");
			}
			if (arg0.equals("__key")){
				return (Comparable)getKey();
			} else if (arg0.equals("__value")) {
				return (Comparable)getValue();
			}
			String methodName = "get" + arg0.substring(0, 1).toUpperCase() + arg0.substring(1);
			Method m = entry.getValue().getClass().getDeclaredMethod(
					methodName, (Class<?>[])null);
			return (Comparable)m.invoke(entry.getValue(), null);
		}
		catch (Throwable e) {
			System.err.println("GetAttr " + arg0);
			System.err.println(entry);
			e.printStackTrace(System.err);
			throw new QueryException(e);
		}
	}

	@Override
	public AttributeType getAttributeType(String arg0) {
		return null;
	}

	@Override
	public Object getKey() {
		return entry.getKey();
	}

	@Override
	public Object getValue() {
		return entry.getValue();
	}
}