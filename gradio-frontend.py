import gradio as gr
import random
from assistant import predict, validate_user, register_user


# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as demo:
    
    gr.Markdown(
            """# Welcome to Visionnaire: A Personalized AI Assistant 
            Please login or register to continue.
            """
        )
    
    history = gr.State(value=[])
    user_id = gr.State(value="")
    
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
        with gr.Row():
            user_id_input = gr.Textbox(
                    label="Enter your User ID",
                    placeholder="e.g., USER001",
                    scale=4
            )
            login_button = gr.Button("🔑 Login", scale=1)
        login_message = gr.Markdown()
        
    # Registration Section (initially invisible)
    with gr.Group(visible=False) as register_section:
        gr.Markdown("## 📝 New User Registration")
        with gr.Column():
            reg_name = gr.Textbox(
                    label="Full Name",
                    placeholder="Enter your full name"
            )
            register_button = gr.Button("📝 Register")
            register_message = gr.Markdown()
    
    # Main Interface (initially invisible)
    with gr.Group(visible=False) as main_interface:
        
        with gr.Group():
            gr.Markdown("## 💬 Chat Interface")
            chatbot = gr.Chatbot(label="Chatbot")
            message_input = gr.Textbox(label="Your Message", placeholder="Type your message here", scale=4)
            send_button = gr.Button("Send")

    
    def show_login():
        return {login_section: gr.Group(visible=True), register_section: gr.Group(visible=False), main_interface: gr.Group(visible=False)}
    
    def show_register():
        return {login_section: gr.Group(visible=False), register_section: gr.Group(visible=True), main_interface: gr.Group(visible=False)}
    
    login_tab_btn.click(show_login, outputs=[login_section, register_section, main_interface])
    register_tab_btn.click(show_register, outputs=[login_section, register_section, main_interface])

    # Login Logic
    def login(user_id):
        success, message = validate_user(user_id)
        if success:
            return {login_message: gr.Markdown(f"✅ {message}"), main_interface: gr.Group(visible=True), chatbot: [], history: []}
        return {login_message: gr.Markdown(f"❌ {message}"), main_interface: gr.Group(visible=False)}
    
    login_button.click(login, inputs=[user_id_input], outputs=[login_message, main_interface, chatbot, history])

    # Registration Logic
    def register(name): 
        if not name: 
            return gr.Markdown("❌ Please fill in all required fields.")
        success, message = register_user(name) 
        if success:
            return gr.Markdown(f"✅ {message}\nPlease go to the login tab and use this ID to log in.")
        return gr.Markdown(f"❌ {message}")
    
    register_button.click(register, inputs=[reg_name], outputs=[register_message])
        
    send_button.click(
        predict,
        inputs=[message_input, history, user_id_input],
        outputs=[chatbot, history]  # Update both Chatbot and internal state
    )

demo.launch(share = True)
