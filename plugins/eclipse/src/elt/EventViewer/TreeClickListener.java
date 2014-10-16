package elt.EventViewer;

import org.eclipse.jface.viewers.DoubleClickEvent;
import org.eclipse.jface.viewers.IDoubleClickListener;
import org.eclipse.jface.viewers.TreeSelection;
import org.eclipse.jface.viewers.TreeViewer;
import org.w3c.dom.Node;

public class TreeClickListener implements IDoubleClickListener {
		
		public void doubleClick(DoubleClickEvent event) {
			TreeSelection ts = (TreeSelection)event.getSelection();
			Object obj = ts.getFirstElement();
			if (obj instanceof Node) {
				Node node = (Node)obj;
				boolean state = ((TreeViewer)event.getViewer()).
						getExpandedState(node);
				if (state) 
					((TreeViewer)event.getViewer()).collapseToLevel(node, 1);
				else
					((TreeViewer)event.getViewer()).expandToLevel(node, 1);
			}
		}
}