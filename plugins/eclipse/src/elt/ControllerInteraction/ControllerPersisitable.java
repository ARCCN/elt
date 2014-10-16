package elt.ControllerInteraction;

import org.eclipse.ui.IMemento;
import org.eclipse.ui.IPersistableElement;

public class ControllerPersisitable implements IPersistableElement {

	@Override
	public void saveState(IMemento memento) {
		// TODO Auto-generated method stub
		//System.out.println("pers savestate");
	}

	@Override
	public String getFactoryId() {
		// TODO Auto-generated method stub
		//System.out.println("pers getid");
		return "org.eclipse.ui.elt.ControllerElementFactory";
	}

}
