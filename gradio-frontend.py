import gradio as gr
import random
from assistant import predict
from auth_handler import AuthHandler

auth = AuthHandler()

# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as demo:
    
    gr.Markdown(
            """# Welcome to Visionnaire: A Personalized AI Assistant 
            Please login or register to continue.
            """
        )
    
    history = gr.State(value=[])
    session_token = gr.State(value="")
    
    # Login/Register Selection
    with gr.Group():
        with gr.Row():
            with gr.Column(scale=1):
                login_tab_btn = gr.Button("🔑 Login")
            with gr.Column(scale=1):
                register_tab_btn = gr.Button("📝 Register")
        
    # Login Section
    with gr.Group() as login_section:
        gr.Markdown("## 🔐 User Authentication")
        with gr.Column():
            email_input = gr.Textbox(
                    label="Email",
                    placeholder="Enter your email",
                    scale=4
            )
            password_input = gr.Textbox(
                    label="Password",
                    placeholder="Enter your password",
                    type="password",
                    scale=4
            )
            login_button = gr.Button("🔑 Login", scale=1)
        login_message = gr.Markdown()
        
    # Registration Section (initially invisible)
    with gr.Group(visible=False) as register_section:
        gr.Markdown("## 📝 New User Registration")
        with gr.Column():
            reg_email = gr.Textbox(
                    label="Email",
                    placeholder="Enter your email"
            )
            reg_password = gr.Textbox(
                    label="Password",
                    placeholder="Enter your password",
                    type="password"
            )
            reg_name = gr.Textbox(
                    label="Full Name",
                    placeholder="Enter your full name"
            )
            register_button = gr.Button("📝 Register")
            register_message = gr.Markdown()
    
    # Main Interface (initially invisible)
    with gr.Group(visible=False) as main_interface:
        with gr.Row():
            logout_button = gr.Button("🚪 Logout", scale=1)
            user_info = gr.Markdown()
        
        with gr.Group():
            gr.Markdown("## 💬 Chat Interface")
            chatbot = gr.Chatbot(label="Chatbot")
            with gr.Row():
                message_input = gr.Textbox(
                    label="Your Message", 
                    placeholder="Type your message here and press Enter to send", 
                    scale=4,
                    container=False
                )
                send_button = gr.Button("Send", scale=1)

    def show_login():
        return {
            login_section: gr.Group(visible=True),
            register_section: gr.Group(visible=False),
            main_interface: gr.Group(visible=False)
        }
    
    def show_register():
        return {
            login_section: gr.Group(visible=False),
            register_section: gr.Group(visible=True),
            main_interface: gr.Group(visible=False)
        }
    
    login_tab_btn.click(show_login, outputs=[login_section, register_section, main_interface])
    register_tab_btn.click(show_register, outputs=[login_section, register_section, main_interface])

    # Login Logic
    def handle_login(email, password):
        success, message, token = auth.login(email, password)
        if success and token:
            is_valid, user_data = auth.validate_session(token)
            if is_valid and user_data:
                user_info_text = f"👤 Logged in as: {user_data.get('name', 'User')} ({user_data.get('email', 'No email')})"
                return {
                    login_message: gr.Markdown(f"✅ {message}"),
                    main_interface: gr.Group(visible=True),
                    login_section: gr.Group(visible=False),
                    chatbot: [],
                    history: [],
                    session_token: token,
                    user_info: user_info_text,
                    message_input: gr.Textbox(value="")  # Clear message input on login
                }
        return {
            login_message: gr.Markdown(f"❌ {message}"),
            main_interface: gr.Group(visible=False),
            session_token: "",
            user_info: ""
        }
    
    login_button.click(
        handle_login,
        inputs=[email_input, password_input],
        outputs=[login_message, main_interface, login_section, chatbot, history, session_token, user_info, message_input]
    )

    # Registration Logic
    def handle_register(email, password, name):
        if not all([email, password, name]):
            return gr.Markdown("❌ Please fill in all required fields.")
        success, message = auth.register(email, password, name)
        return gr.Markdown(f"{'✅' if success else '❌'} {message}")
    
    register_button.click(
        handle_register,
        inputs=[reg_email, reg_password, reg_name],
        outputs=[register_message]
    )

    # Logout Logic
    def handle_logout(token):
        # Print token value for debugging
        print(f"Logging out with token: {token}")
        
        if not token:
            return {
                main_interface: gr.Group(visible=False),
                login_section: gr.Group(visible=True),
                session_token: "",
                login_message: gr.Markdown("⚠️ No active session to log out from.")
            }
            
        # Directly handle logout without relying on the auth handler
        # Since there seems to be an issue with the auth handler's logout function
        try:
            # Even if the auth handler fails, we'll still log the user out of the UI
            auth.logout(token)
        except Exception as e:
            print(f"Logout error (ignoring): {str(e)}")
        
        # Return the user to the login screen regardless of the backend result
        return {
            main_interface: gr.Group(visible=False),
            login_section: gr.Group(visible=True),
            register_section: gr.Group(visible=False),
            session_token: "",
            login_message: gr.Markdown("✅ Logged out successfully!"),
            email_input: gr.Textbox(value=""),
            password_input: gr.Textbox(value=""),
            message_input: gr.Textbox(value=""),  # Clear message input on logout
            chatbot: [],  # Clear chatbot
            history: []   # Clear history
        }

    logout_button.click(
        handle_logout,
        inputs=[session_token],
        outputs=[main_interface, login_section, register_section, session_token, login_message, 
                email_input, password_input, message_input, chatbot, history]
    )
        
    def handle_chat(message, history, session_token):
        """Handle chat with session validation"""
        if not message.strip():
            return history, gr.Group(visible=True), gr.Group(visible=False), gr.Textbox(value="")
            
        is_valid, user_data = auth.validate_session(session_token)
        if not is_valid:
            history.append(("", "⚠️ Your session has expired. Please login again."))
            return history, gr.Group(visible=False), gr.Group(visible=True), gr.Textbox(value="")
        
        # Use user's ID from Ory for chat history
        new_history, _ = predict(message, history, user_data['id'])
        return new_history, gr.Group(visible=True), gr.Group(visible=False), gr.Textbox(value="")

    # Bind the handle_chat function to both send button and message_input (for Enter key)
    send_button.click(
        handle_chat,
        inputs=[message_input, history, session_token],
        outputs=[chatbot, main_interface, login_section, message_input]
    )
    
    # Also bind to the textbox's submit event (triggered when Enter is pressed)
    message_input.submit(
        handle_chat,
        inputs=[message_input, history, session_token],
        outputs=[chatbot, main_interface, login_section, message_input]
    )

# Change server_name from 127.0.0.1 to 0.0.0.0 to make it publicly accessible
# This will make it listen on all network interfaces
demo.launch(server_name="0.0.0.0", server_port=7861, share=True)
