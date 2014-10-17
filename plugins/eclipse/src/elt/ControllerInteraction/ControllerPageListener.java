package elt.ControllerInteraction;

import org.eclipse.jface.dialogs.IPageChangedListener;
import org.eclipse.jface.dialogs.PageChangedEvent;

public class ControllerPageListener implements IPageChangedListener {

	protected ControllerEditor editor;
	
	public ControllerPageListener(ControllerEditor e) {
		editor = e;
	}
	
	@Override
	public void pageChanged(PageChangedEvent event) {
		editor.pageChanged(event);
	}

}
