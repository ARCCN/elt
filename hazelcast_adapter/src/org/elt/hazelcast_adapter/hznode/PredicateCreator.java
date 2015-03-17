package org.elt.hazelcast_adapter.hznode;

import java.util.Iterator;
import java.util.Map.Entry;
import java.util.Set;

import org.elt.hazelcast_adapter.FlowModMessage;
import org.elt.hazelcast_adapter.of.MatchPart;

import com.hazelcast.query.EntryObject;
import com.hazelcast.query.Predicate;
import com.hazelcast.query.PredicateBuilder;
import com.hazelcast.query.Predicates.AbstractPredicate;
import com.hazelcast.query.Predicates.AndPredicate;
import com.hazelcast.query.Predicates.OrPredicate;
import com.hazelcast.query.impl.Index;
import com.hazelcast.query.impl.QueryContext;
import com.hazelcast.query.impl.QueryableEntry;

public class PredicateCreator {
	
	public static class CompareTagAppsFirst extends AbstractPredicate {

		private static final long serialVersionUID = 5940462640977853145L;
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
			if (!it.hasNext() || it.next().equalsIgnoreCase((String)value))
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
		EntryObject e1 = new PredicateBuilder().getEntryObject();
		Predicate p, p1;
	
		if (msg.getFlowMod().isStrict()) {
			p = e.key().equal(mp);
			if (v.getTag().getAppsLength() == 1) {
				Predicate my_p = new CompareTagAppsFirst("", v.getTag().getApps().iterator().next());
				p1 = e1.get("tag").get("appsLength").greaterThan(1);
				p1 = new OrPredicate(p1, my_p);
				p = new AndPredicate(p1, p);
			}
		} else {
			p = e.key().greaterEqual(mp);
			if (v.getTag().getAppsLength() == 1) {
				Predicate my_p = new CompareTagAppsFirst("", v.getTag().getApps().iterator().next());
				p1 = e1.get("tag").get("appsLength").greaterThan(1);
				p1 = new OrPredicate(p1, my_p);
				p = new AndPredicate(p1, p);
			}
		}
		return p;
	}
}
