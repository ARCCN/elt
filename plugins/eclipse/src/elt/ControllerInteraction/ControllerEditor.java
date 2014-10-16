package elt.ControllerInteraction;

import java.util.Vector;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.ui.IMemento;
import org.eclipse.ui.IPersistableEditor;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.forms.editor.FormEditor;

public class ControllerEditor extends FormEditor implements IPersistableEditor {

	protected Vector<ControllerPage> pagesToLoad = new Vector<ControllerPage>();
	
	@Override
	protected void addPages() {
		// TODO Auto-generated method stub
		try {
			if (pagesToLoad.size() == 0)
				addPage(new ControllerPage(this, "controller_page_1", "Controller"));
			else {
				for (ControllerPage page: pagesToLoad) {
					addPage(page);
				}
			}
		} catch (PartInitException e) {
			//
		}
	}

	@Override
	public void doSave(IProgressMonitor monitor) {
		// TODO Auto-generated method stub

	}

	@Override
	public void doSaveAs() {
		// TODO Auto-generated method stub

	}

	@Override
	public boolean isSaveAsAllowed() {
		// TODO Auto-generated method stub
		return false;
	}

	@Override
	public void saveState(IMemento memento) {
		for (Object p: this.pages) {
			if (p instanceof ControllerPage) {
				ControllerPage page = (ControllerPage)p;
				page.dumpState();
				IMemento child = memento.createChild("ControllerPage", page.getId());
				child.putString("destUri", page.destUri);
				child.putString("title", page.getTitle());
			}
		}
	}

	@Override
	public void restoreState(IMemento memento) {
		for (IMemento child: memento.getChildren("ControllerPage")) {
			ControllerPage page = new ControllerPage(
					this, child.getID(), child.getString("title"));
			page.destUri = child.getString("destUri");
			pagesToLoad.add(page);
		}		
	}

}
