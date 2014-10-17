package elt.ControllerInteraction;

import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IPersistableElement;

public class ControllerInput implements IEditorInput {
	// TODO: Multiple controllers!

	public ControllerInput() {
	}
	
	public boolean equals(Object obj) {
		if (obj instanceof ControllerInput) {
			return true;
		}
		return false;
	}
	
	@Override
	public Object getAdapter(Class adapter) {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public boolean exists() {
		// TODO Auto-generated method stub
		return true;
	}

	@Override
	public ImageDescriptor getImageDescriptor() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public String getName() {
		// TODO Auto-generated method stub
		return "Controller";
	}

	@Override
	public IPersistableElement getPersistable() {
		// TODO Auto-generated method stub
		return new ControllerPersisitable();
	}

	@Override
	public String getToolTipText() {
		// TODO Auto-generated method stub
		return "Controller interaction";
	}

}
