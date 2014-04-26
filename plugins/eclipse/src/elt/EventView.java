package elt;

import java.util.ArrayList;

import org.eclipse.jface.viewers.StructuredSelection;
import org.eclipse.jface.viewers.TreeSelection;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.part.ViewPart;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class EventView extends ViewPart {
	protected XMLLabelProvider labelProvider;
	protected XMLContentProvider contentProvider;
	protected TreeViewer eventViewer;
	protected Node root;
	
	@Override
	public void createPartControl(Composite parent) {
		GridLayout layout = new GridLayout();
		layout.numColumns = 1;
		layout.verticalSpacing = 2;
		layout.marginWidth = 0;
		layout.marginHeight = 2;
		parent.setLayout(layout);
		
		eventViewer = new TreeViewer(parent);
		contentProvider = new XMLContentProvider("entry");
		eventViewer.setContentProvider(contentProvider);
		labelProvider = new XMLLabelProvider();
		eventViewer.setLabelProvider(labelProvider);
		eventViewer.setUseHashlookup(true);
		eventViewer.addSelectionChangedListener(new EntrySelectionListener());
		eventViewer.addDoubleClickListener(new TreeClickListener());
		
		GridData layoutData = new GridData();
		layoutData.grabExcessHorizontalSpace = true;
		layoutData.grabExcessVerticalSpace = true;
		layoutData.horizontalAlignment = GridData.FILL;
		layoutData.verticalAlignment = GridData.FILL;
		layoutData.widthHint = 300;
		eventViewer.getControl().setLayoutData(layoutData);
	}
	
	public void setEventViewerInput(Node node)
	{
		Object obj = ((TreeSelection)eventViewer.getSelection()).getFirstElement();
		Node selection = null;
		if (obj != null && node != null && root != null) {
			// We remember the path to selected entry.
			Node current = (Node)obj;
			// Tags.
			ArrayList<String> path = new ArrayList<String>();
			// Indices in elements with equal tag.
			ArrayList<Integer> path_index = new ArrayList<Integer>();
			while (current != root) {
				path.add(current.getNodeName());
				NodeList children = current.getParentNode().getChildNodes();
				int tag_index = 0;
				for (int i = 0; i < children.getLength(); ++i) {
					if (children.item(i).isSameNode(current)) {
						path_index.add(tag_index);
						break;
					}
					if (children.item(i).getNodeName().equalsIgnoreCase(current.getNodeName()))
						++tag_index;
				}
				current = current.getParentNode();
			}
			current = node;
			for (int i = path.size()-1; i >= 0; --i) {
				if (current == null)
					break;
				current = Util.getChildWithIndex(current, path.get(i), path_index.get(i));
			}
			if (current != null) {
				selection = current;
			}
		}
		eventViewer.setInput(node);
		if (selection != null)
			eventViewer.setSelection(new StructuredSelection(selection), true);
		root = node;
		if (node == null) {
			try {
				CodeView view = (CodeView)PlatformUI.getWorkbench().
						getActiveWorkbenchWindow().getActivePage().
						showView("elt.CodeView");
				view.setCodeViewerInput(null);
				DataView dview = (DataView)PlatformUI.getWorkbench().
						getActiveWorkbenchWindow().getActivePage().
						showView("elt.DataView");
				dview.setDataViewerInput(null);
			}
			catch(Exception e) {
				e.printStackTrace();
			}
		}
		eventViewer.expandAll();
	}
	
	@Override
	public void setFocus() {
		// TODO Auto-generated method stub

	}

}
