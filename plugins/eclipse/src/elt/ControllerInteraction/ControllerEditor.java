package elt.ControllerInteraction;

import java.util.Vector;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.jface.dialogs.PageChangedEvent;
import org.eclipse.swt.widgets.MessageBox;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IMemento;
import org.eclipse.ui.IPersistableEditor;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.forms.editor.FormEditor;
import org.eclipse.ui.forms.editor.FormPage;

public class ControllerEditor extends FormEditor implements IPersistableEditor {

	protected Vector<ControllerPage> pagesToLoad = new Vector<ControllerPage>();
	protected int max_index = 0;
	
	@Override
	protected void addPages() {
		try {
			if (pagesToLoad.size() == 0) {
				max_index = 1;
				addPage(new ControllerPage(this, "controller_page_" + max_index, 
						"Controller_" + max_index));
				addPage(new FormPage(this, "new_page", "+"));
				this.addPageChangedListener(new ControllerPageListener(this));
			} else {
				for (ControllerPage page: pagesToLoad) {
					addPage(page);
				}
				pagesToLoad.clear();
				addPage(new FormPage(this, "new_page", "+"));
				this.addPageChangedListener(new ControllerPageListener(this));
			}
		} catch (PartInitException e) {}
	}
	
	protected void createNewPage() {
		++max_index;
		try{	
			addPage(this.getActivePage(), new ControllerPage(this, "controller_page_" + max_index, 
					"Controller_" + max_index));
			this.setActivePage("controller_page_" + max_index);
		} catch (PartInitException e) {}
	}
	
	protected void pageChanged(PageChangedEvent e) {
		Object page = e.getSelectedPage();
		if (page instanceof FormPage && ((FormPage)page).getId() == "new_page") {
			this.createNewPage();
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
				try {
					// Lazy initialization!
					page.dumpState();
				} catch (Throwable e) {}
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
			if (page.getId().startsWith("controller_page_")) {
				int index = Integer.parseInt(
						page.getId().replaceFirst("controller_page_", ""));
				if (index > max_index)
					max_index = index;
			}
		}		
	}

}
