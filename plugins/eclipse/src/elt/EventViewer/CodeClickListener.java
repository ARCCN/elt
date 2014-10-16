package elt.EventViewer;

import org.eclipse.jface.viewers.DoubleClickEvent;
import org.eclipse.jface.viewers.IDoubleClickListener;
import org.eclipse.jface.viewers.TreeSelection;
import org.eclipse.jface.viewers.TreeViewer;
import org.w3c.dom.Node;

public class CodeClickListener implements IDoubleClickListener {
		protected CodeView parent;
		
		public CodeClickListener(CodeView p) {
			super();
			parent = p;
		}
		
		public void doubleClick(DoubleClickEvent event) {
			TreeSelection ts = (TreeSelection)event.getSelection();
			Object obj = ts.getFirstElement();
			if (obj instanceof Node) {
				Node node = (Node)obj;
				if (node.getNodeName().equalsIgnoreCase("call")) {
					parent.openFile(node);
				}
				else if (node.getNodeName().equalsIgnoreCase("module") ||
					node.getNodeName().equalsIgnoreCase("line")) {
					parent.openFile(node.getParentNode());
				}
				else {
					boolean state = ((TreeViewer)event.getViewer()).
							getExpandedState(node);
					if (state) 
						((TreeViewer)event.getViewer()).collapseToLevel(node, 1);
					else
						((TreeViewer)event.getViewer()).expandToLevel(node, 1);
				}
			}
		}
}