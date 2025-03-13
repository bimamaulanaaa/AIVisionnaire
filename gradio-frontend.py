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
            message_input = gr.Textbox(label="Your Message", placeholder="Type your message here", scale=4)
            send_button = gr.Button("Send")

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
        if success:
            is_valid, user_data = auth.validate_session(token)
            if is_valid:
                user_info_text = f"👤 Logged in as: {user_data['name']} ({user_data['email']})"
                return {
                    login_message: gr.Markdown(f"✅ {message}"),
                    main_interface: gr.Group(visible=True),
                    chatbot: [],
                    history: [],
                    session_token: token,
                    user_info: user_info_text
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
        outputs=[login_message, main_interface, chatbot, history, session_token, user_info]
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
    def handle_logout(session_token):
        success, message = auth.logout(session_token)
        if success:
            return {
                main_interface: gr.Group(visible=False),
                login_section: gr.Group(visible=True),
                session_token: "",
                login_message: gr.Markdown("✅ Logged out successfully!")
            }
        return {
            login_message: gr.Markdown(f"❌ {message}")
        }

    logout_button.click(
        handle_logout,
        inputs=[session_token],
        outputs=[main_interface, login_section, session_token, login_message]
    )
        
    def handle_chat(message, history, session_token):
        """Handle chat with session validation"""
        is_valid, user_data = auth.validate_session(session_token)
        if not is_valid:
            history.append(("", "⚠️ Your session has expired. Please login again."))
            return history, gr.Group(visible=False), gr.Group(visible=True)
        
        # Use user's ID from Ory for chat history
        new_history, _ = predict(message, history, user_data['id'])
        return new_history, gr.Group(visible=True), gr.Group(visible=False)

    send_button.click(
        handle_chat,
        inputs=[message_input, history, session_token],
        outputs=[chatbot, main_interface, login_section]
    )

demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
