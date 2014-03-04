package elt;

import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.part.ViewPart;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class DataView extends ViewPart {
	protected XMLLabelProvider labelProvider;
	protected XMLContentProvider contentProvider;
	protected TreeViewer dataViewer;
	
	@Override
	public void createPartControl(Composite parent) {
		GridLayout layout = new GridLayout();
		layout.numColumns = 1;
		layout.verticalSpacing = 2;
		layout.marginWidth = 0;
		layout.marginHeight = 2;
		parent.setLayout(layout);
		
		dataViewer = new TreeViewer(parent);
		contentProvider = new XMLContentProvider(null);
		dataViewer.setContentProvider(contentProvider);
		labelProvider = new XMLLabelProvider();
		dataViewer.setLabelProvider(labelProvider);
		dataViewer.setUseHashlookup(true);
		dataViewer.addDoubleClickListener(new TreeClickListener());
		
		GridData layoutData = new GridData();
		layoutData.grabExcessHorizontalSpace = true;
		layoutData.grabExcessVerticalSpace = true;
		layoutData.horizontalAlignment = GridData.FILL;
		layoutData.verticalAlignment = GridData.FILL;
		layoutData.widthHint = 300;
		dataViewer.getControl().setLayoutData(layoutData);
	}
	
	public void setDataViewerInput(Node node)
	{
		dataViewer.setInput(node);
		dataViewer.expandAll();
	}
	
	public Node getChild(Node n, String name) {
		NodeList c = n.getChildNodes();
		for (int i = 0; i < c.getLength(); i++) {
			if (c.item(i).getNodeName().equalsIgnoreCase(name)) {
				return c.item(i);
			}
		}
		return null;
	}
	
	@Override
	public void setFocus() {
		// TODO Auto-generated method stub

	}

}
