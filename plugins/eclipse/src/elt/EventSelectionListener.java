package elt;

import org.eclipse.jface.viewers.ISelectionChangedListener;
import org.eclipse.jface.viewers.SelectionChangedEvent;
import org.eclipse.jface.viewers.TreeSelection;
import org.eclipse.ui.PlatformUI;
import org.w3c.dom.Node;


public class EventSelectionListener implements ISelectionChangedListener {		
		
		public void selectionChanged(SelectionChangedEvent event) {
			TreeSelection ts = (TreeSelection)event.getSelection();
			Object obj = ts.getFirstElement();
			if (obj instanceof Node) {
				Node node = (Node)obj;
				if (node.getNodeName().equalsIgnoreCase("event")) {
					try {
						EventView view = (EventView)PlatformUI.getWorkbench().
							getActiveWorkbenchWindow().getActivePage().
							showView("org.eclipse.ui.elt.EventView");
						view.setEventViewerInput(node);
					}
					catch(Exception e) {e.printStackTrace();}
				}
				else
				{
					try {
						EventView view = (EventView)PlatformUI.getWorkbench().
							getActiveWorkbenchWindow().getActivePage().
							showView("org.eclipse.ui.elt.EventView");
						view.setEventViewerInput(null);
					}
					catch(Exception e) {e.printStackTrace();}
				}
			}
		}
}	