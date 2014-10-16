package elt.ControllerInteraction;

import org.eclipse.core.runtime.IAdaptable;
import org.eclipse.ui.IElementFactory;
import org.eclipse.ui.IMemento;

public class ControllerElementFactory implements IElementFactory {

	@Override
	public IAdaptable createElement(IMemento memento) {
		// TODO Auto-generated method stub
		return new ControllerInput();
	}

}
