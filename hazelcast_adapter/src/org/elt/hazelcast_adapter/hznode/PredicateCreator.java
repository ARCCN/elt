package org.elt.hazelcast_adapter.hznode;

import java.util.Iterator;
import java.util.Set;
import java.util.Map.Entry;

import org.elt.hazelcast_adapter.FlowModMessage;
import org.elt.hazelcast_adapter.of.MatchPart;

import com.hazelcast.query.EntryObject;
import com.hazelcast.query.Predicate;
import com.hazelcast.query.PredicateBuilder;
import com.hazelcast.query.Predicates.AbstractPredicate;
import com.hazelcast.query.impl.Index;
import com.hazelcast.query.impl.QueryContext;
import com.hazelcast.query.impl.QueryableEntry;

public class PredicateCreator {
	
	public static class CompareTagAppsFirst extends AbstractPredicate {
		protected Comparable value;
		
		CompareTagAppsFirst() {}
		CompareTagAppsFirst(String attribute) { super(attribute); }
		public CompareTagAppsFirst(String attribute, Comparable value) {
            super(attribute);
            this.value = value;
        }
		
		@Override
		public boolean apply(Entry mapEntry) {
			//Comparable entryValue = readAttribute(mapEntry);
			Iterator<String> it = ((TableValue)mapEntry.getValue()).getTag().getApps().iterator();
			if (!it.hasNext() || it.next() == value)
				return false;
			return true;
		}

		@Override
		public Set<QueryableEntry> filter(QueryContext queryContext) {
			Index index = getIndex(queryContext);
			index.getRecords(value);
			return null;
		}
		
	}
	
	public static Predicate createPredicate(FlowModMessage msg) {
		// TODO: Create predicate.
		MatchPart mp = msg.getMatchPart();
		TableValue v = msg.getTableValue();
		EntryObject e = new PredicateBuilder().getEntryObject();
		Predicate p;
		if (msg.getFlowMod().isStrict()) {
			p = e.key().equal(mp);
			if (v.getTag().apps_length == 1) {
				p = e.get("tag").get("apps_length").greaterThan(1).
							or(new CompareTagAppsFirst(v.getTag().getApps().iterator().next())).and(p);
			}
		} else {
			p = e.key().greaterEqual(mp);
			if (v.getTag().apps_length == 1) {
				p = e.get("tag").get("apps_length").greaterThan(1).
							or(new CompareTagAppsFirst(v.getTag().getApps().iterator().next())).and(p);
			}
		}
		return p;
	}
}
