package elt;

import org.eclipse.jface.viewers.ISelectionChangedListener;
import org.eclipse.jface.viewers.SelectionChangedEvent;
import org.eclipse.jface.viewers.TreeSelection;
import org.eclipse.ui.PlatformUI;
import org.w3c.dom.Node;


public class EntrySelectionListener implements ISelectionChangedListener {
		
		public void selectionChanged(SelectionChangedEvent event) {
			TreeSelection ts = (TreeSelection)event.getSelection();
			Object obj = ts.getFirstElement();
			if (obj instanceof Node) {
				Node node = (Node)obj;
				if (node.getNodeName().equalsIgnoreCase("entry")) {
					try {
						CodeView cview = (CodeView)PlatformUI.getWorkbench().
							getActiveWorkbenchWindow().getActivePage().
							showView("elt.CodeView");
						cview.setCodeViewerInput(Util.getChild(node, "code"));
						DataView dview = (DataView)PlatformUI.getWorkbench().
								getActiveWorkbenchWindow().getActivePage().
								showView("elt.DataView");
						Node data = Util.getChild(node, "ofp_flow_mod");
						if (data == null) {
							data = Util.getChild(node, "rule");
						}
						dview.setDataViewerInput(data);
					}
					catch(Exception e) {e.printStackTrace();}
				}
				else
				{
					try {
						CodeView cview = (CodeView)PlatformUI.getWorkbench().
							getActiveWorkbenchWindow().getActivePage().
							showView("elt.CodeView");
						cview.setCodeViewerInput(null);
						DataView dview = (DataView)PlatformUI.getWorkbench().
								getActiveWorkbenchWindow().getActivePage().
								showView("elt.DataView");
						dview.setDataViewerInput(null);
					}
					catch(Exception e) {e.printStackTrace();}
				}
			}
		}
}	