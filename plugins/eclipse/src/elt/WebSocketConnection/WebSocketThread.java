package elt.WebSocketConnection;

import java.net.URI;
import java.util.concurrent.TimeUnit;

import org.eclipse.jetty.websocket.client.ClientUpgradeRequest;
import org.eclipse.jetty.websocket.client.WebSocketClient;
import org.eclipse.swt.widgets.Display;

public class WebSocketThread implements Runnable, INotified {

	protected String uri;
	protected INotified gui;
	
	public WebSocketThread(String uri, INotified gui) {
		this.uri = uri;
		this.gui = gui;
	}
	
	@Override
	public void run() {
		WebSocketClient client = new WebSocketClient();
		WSocket socket = new WSocket(this);
		try {
            client.start();
            URI echoUri = new URI(this.uri);
            ClientUpgradeRequest request = new ClientUpgradeRequest();
            client.connect(socket, echoUri, request);
            
            //System.out.printf("Connecting to : %s%n", echoUri);
            socket.awaitConnect(5, TimeUnit.SECONDS);
            if (!socket.connected) {
            	sendMessage("ConnectionError");
            	return;
            }
            processMessage("SocketConnected", socket);
            socket.awaitClose(100000, TimeUnit.DAYS);
		} catch (InterruptedException t) {
        } catch (Throwable t) {
            t.printStackTrace();
        } finally {
            try {
                client.stop();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

	}
		
	class MsgSendRunnable implements Runnable {
		
		private INotified recv;
		private String msg;
		private Object data;
		
		public MsgSendRunnable(INotified recv, String msg, Object data) {
			this.recv = recv;
			this.msg = msg;
			this.data = data;
		}
		
		public void run() {
			this.recv.processMessage(msg, data);
		}
	}
	
	public void processMessage(String msg, Object data) {
		if (msg.equals("DataReceived")) {
			Display display = Display.getDefault();
			display.asyncExec(
				new MsgSendRunnable(this.gui, msg, data)
			);
		} else if (msg.equals("SocketConnected")) {
			Display display = Display.getDefault();
			display.asyncExec(
				new MsgSendRunnable(this.gui, msg, data)
			);
		} else if (msg.equals("SocketDisconnected")) {
			Display display = Display.getDefault();
			display.asyncExec(
				new MsgSendRunnable(this.gui, msg, data)
			);
		}
	}
	
	public void sendMessage(String msg) {
		Display display = Display.getDefault();
		display.asyncExec(
			new MsgSendRunnable(this.gui, msg, null)
		);
	}

}
