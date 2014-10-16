package elt.ControllerInteraction.Messages;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class MessageRegistry {
	protected Map <String, Class<? extends ControllerMessage>> map;
	
	public MessageRegistry() {
		map = createMap();
	}
	
	protected static Map <String, Class<? extends ControllerMessage>> createMap() {
		HashMap<String, Class<? extends ControllerMessage>> map = 
				new HashMap<String, Class<? extends ControllerMessage>>();
		ArrayList<Class<? extends ControllerMessage>> classList = 
				new ArrayList<Class<? extends ControllerMessage>>();
		
		// TODO: More safe approach?
		// Now we should keep track on protocol change!
		classList.add(ControllerMessage.class);
		classList.add(ControllerStatus.class);
		classList.add(GetControllerComponents.class);
		classList.add(ControllerComponents.class);
		classList.add(LaunchComponent.class);
		classList.add(LaunchSingle.class);
		classList.add(LaunchHierarchical.class);
		classList.add(StartController.class);
		classList.add(StopController.class);
		classList.add(ComponentLaunched.class);
		
		for (Class<? extends ControllerMessage> c: classList) {
			try {
				map.put((String)c.getField("_name").get(null), c);
			} catch (NoSuchFieldException | SecurityException | 
					IllegalAccessException e) {
				System.out.println(c);
			}
		}
		return map;
	}
	
	public static Class<? extends ControllerMessage> getClass(String _name) {
		return new MessageRegistry().get(_name);
	}
	
	public Class<? extends ControllerMessage> get(String _name) {
		return map.get(_name);
	}
}
