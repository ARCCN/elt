package elt.EventViewer;

import org.eclipse.jface.viewers.Viewer;
import org.eclipse.jface.viewers.ViewerComparator;
import org.w3c.dom.Node;

public class XmlLogComparator extends ViewerComparator {
	public XmlLogComparator(boolean reverse) {
		super();
		this.reverse = reverse;
	}
	
	private CompareNodesByTimestamp comparator = new CompareNodesByTimestamp();
	private boolean reverse = false;
	
	public int compare(Viewer viewer, Object e1, Object e2) {
		Node xml1 = (Node) e1;
		Node xml2 = (Node) e2;
		int result;
		// We compare only events, because they should be compared by time stamps.
		if (xml1.getNodeName() == "event" &&
				xml2.getNodeName() == "event") {
			result = comparator.compare(xml1, xml2);
		} else {
			result = super.compare(viewer, e1, e2);
		}
		if (reverse) {
			return -result;
		}
		return result;
	}
}
