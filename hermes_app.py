from functions.utils import generate_pdp, format_pdp_text, load_product_details, format_product_details, retailer_customize_pdp
import streamlit as st
import os
import json


# DATA 
DATA_FOLDER_PATH = os.path.join(os.getcwd(), "data")
assert os.path.exists(DATA_FOLDER_PATH)

# Load brand knowledge 
with open(os.path.join(DATA_FOLDER_PATH, "brand_data", "brand_knowledge.txt"), "r") as f:
    brand_knowledge = f.read()
    
# Load persona
with open(os.path.join(DATA_FOLDER_PATH, "persona", "persona.txt"), "r") as f:
    persona = f.read()
    
# Load copywriting guidelines
with open(os.path.join(DATA_FOLDER_PATH, "brand_data", "copywriting_guidelines.txt"), "r") as f:
    copywriting_guidelines = f.read()
    
# Load Plateform Specs
with open(os.path.join(DATA_FOLDER_PATH, "platform_specs", "hermes.txt"), "r") as f:
    hermes_specs = f.read()
    
with open(os.path.join(DATA_FOLDER_PATH, "platform_specs", "sephora.txt"), "r") as f:
    sephora_specs = f.read()
    
# Load product data
product_data = {}  

languages = os.listdir(os.path.join(DATA_FOLDER_PATH, "product_data"))

product_data = {
    language: {
        product[:-4].replace('_', ' ').capitalize().replace('hermes', 'Hermès'): open(os.path.join(DATA_FOLDER_PATH, "product_data", language, product), "r").read() for product in os.listdir(os.path.join(DATA_FOLDER_PATH, "product_data", language))
    } for language in languages
}



# Define the app layout and functionality
def main():
    st.session_state['product_description'] = ""
    st.session_state['object_description'] = ""
    st.session_state["additional_info"] = ""
    st.session_state["product_name"] = ""
    
    # Set font and background color
    st.markdown(
        """
        <style>
        /* Apply background color to the whole app */
        .main {
            background-color: #74899B;
        }
        body, h3, h4, h5, h6, label {
            color: #ffffff;
            font-family: 'Courier New', monospace;
        }
        h1, h2 {
            color: #F37021;
            font-family: 'Courier New', monospace;
        }
        .centered-title {
            text-align: center;
        }
        /* Style the selectbox */
        div[data-baseweb="select"] > div {
            background-color: #74899B !important;
            border: 0.25px solid #ffffff !important;
            font-family: 'Courier New', monospace;
        }
        div[data-baseweb="select"] .css-1wa3eu0-placeholder, div[data-baseweb="select"] .css-1uccc91-singleValue {
            color: #ffffff !important;
            font-family: 'Courier New', monospace;
        }
        div[data-baseweb="select"] .css-1okebmr-indicatorSeparator {
            background-color: #74899B !important;
        }
        div[data-baseweb="select"] .css-tlfecz-indicatorContainer {
            color: #ffffff !important;
        }
        /* Style the text areas */
        .stTextArea textarea {
            background-color: #74899B !important;
            color: #ffffff !important;
            font-family: 'Courier New', monospace;
            border: 0.25px solid #ffffff !important;
        }
        /* Style the button */
        div.stButton button {
            background-color: #74899B !important;
            color: #FFFFFF !important;
            font-family: 'Courier New', monospace;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    left_co, cent_co, last_co = st.columns(3)
    with cent_co:
        st.image("image/hermes.svg", width=300, caption="", output_format="auto")

    st.markdown("<h1 class='centered-title'>L'Écrivain Augmenté</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Write", "Adapt", "Personalize"])

    with tab1:
        st.header("Write PDPs")

        language = st.selectbox("Select Language", ["en", "fr"], index=1)
        st.session_state['language'] = language
        
        product_dict = product_data[language]
        selected_product = st.selectbox("Select an existing product", [""] + list(product_dict.keys()))

        # Text boxes
        if selected_product:
            product_description, object_description, additional_info = load_product_details(selected_product, language)
        else:
            product_description, object_description, additional_info = "", "", ""

        product_name = st.text_area("Product Name", selected_product, height=10)
        product_description = st.text_area("Product Description", product_description, height=200)
        object_description = st.text_area("Object Description", object_description, height=200)
        additional_info = st.text_area("Additional Info", additional_info, height=200)
        st.session_state.product_description = product_description
        st.session_state.object_description = object_description
        st.session_state.additional_info = additional_info
        st.session_state.product_name = product_name
        
        # Save button
        if st.button("Save"):
            st.session_state.product_description = product_description
            st.session_state.object_description = object_description
            st.session_state.additional_info = additional_info
            st.success("Content saved")
        
        product_details = format_product_details(product_description, object_description, additional_info)
        st.session_state['product_details'] = product_details

        # Generate PDP button
        if st.session_state['product_name'] and st.session_state['object_description'] and st.session_state['product_description']:
            if st.button("Write"):
                with st.spinner("Generating PDP..."):
                    pdp_text = generate_pdp(st.session_state.product_name, st.session_state.product_details, st.session_state.language)
                    formatted_pdp_text = format_pdp_text("--- \n\n" + pdp_text)
                    st.success("PDP generated")
                    st.subheader("Generated PDP")
                    st.markdown(
                        """
                        <style>
                        .markdown-text-container {
                            font-family: 'Courier New', monospace;
                            color: #ffffff;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                st.markdown(f'<div class="markdown-text-container">{formatted_pdp_text}</div>', unsafe_allow_html=True)

    with tab2:
        st.header("Retailer Adaptation")
        
        adapt_language = st.selectbox("Select Language", ["en", "fr"])
        st.session_state['adapt_language'] = adapt_language
        
        product_dict = product_data["fr"]
        selected_product_adapt = st.selectbox("Select a product", list(product_dict.keys()))
        st.session_state['selected_product_adapt'] = selected_product_adapt
        
        selected_retailer = st.selectbox("Select a retailer", ["sephora"])
        st.session_state['selected_retailer'] = selected_retailer
        
        if st.button("Adapt"):
            with st.spinner("Adapting PDP..."):
                adapted_pdp_text = retailer_customize_pdp(st.session_state['selected_product_adapt'], st.session_state['adapt_language'])
                st.success("PDP adapted")
                st.subheader("Adapted PDP")
                st.markdown(
                    """
                    <style>
                    .markdown-text-container {
                        font-family: 'Courier New', monospace;
                        color: #ffffff;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(f'<div class="markdown-text-container">{adapted_pdp_text}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

    # with tab1: 
    #     # Product Selection
    #     st.header("Product")
    #     product_category = st.selectbox("Product Category", options=["", "fragrance", "skincare"])
    #     product_name = None
    #     if product_category:
    #         product_name = st.selectbox("Product Name", options=[""] + product_options[product_category])

    #     # Customer Profile Selection
    #     st.header("Customer Profile")
    #     customer_data_path = os.path.join(os.getcwd(), "data", "customer_data")
    #     customer_files = os.listdir(customer_data_path)
    #     customer_profiles = [f.replace('.json', '').replace('_', ' ').capitalize() for f in customer_files]
    #     customer_profile_name = st.selectbox("Select Customer Profile", options=[""] + customer_profiles)

    #     # Load customer profile data
    #     customer_profile = {}
    #     if customer_profile_name:
    #         with open(os.path.join(customer_data_path, customer_profile_name.replace(' ', '_').lower() + '.json')) as f:
    #             customer_profile = json.load(f)

    #     # Target Platform Selection
    #     st.header("Target Platform")
    #     platform_data_path = os.path.join(os.getcwd(), "data", "platform_specs")
    #     platform_files = os.listdir(platform_data_path)
    #     platform_names = [f.replace('.txt', '').replace('_', ' ').capitalize() for f in platform_files]
    #     platform_name = st.selectbox("Select Target Platform", options=[""] + platform_names)

    #     # Personalize Content
    #     st.header("Personalize Content")
    #     # if st.button("Generate Personalized Description"):
    #     #     personalized_text = personalize_content(product_category, product_name, customer_profile, platform_name)
    #     #     st.write(personalized_text)
            
    # with tab2:
    #         st.header("Edit Prompts")
    #         # Select a folder
    #         prompt_base_path = os.path.join(os.getcwd(), "prompts")
    #         folders = os.listdir(prompt_base_path)
    #         prompt_folder = st.selectbox("Select a folder", [""] + folders)

    #         if prompt_folder:
    #             # System Prompt editing
    #             st.subheader("System Prompt")
    #             system_prompt_path = os.path.join(prompt_base_path, prompt_folder, "system_prompt.txt")
    #             system_prompt_content = read_file(system_prompt_path)
    #             system_prompt_text = st.text_area("System Prompt", value=system_prompt_content, height=300)
    #             if system_prompt_text != system_prompt_content:
    #                 if st.button("Save System Prompt"):
    #                     write_file(system_prompt_path, system_prompt_text)

    #             # Human Prompt editing
    #             st.subheader("Human Prompt")
    #             human_prompt_path = os.path.join(prompt_base_path, prompt_folder, "human_prompt.txt")
    #             human_prompt_content = read_file(human_prompt_path)
    #             human_prompt_text = st.text_area("Human Prompt", value=human_prompt_content, height=300)
    #             if human_prompt_text != human_prompt_content:
    #                 if st.button("Save Human Prompt"):
    #                     write_file(human_prompt_path, human_prompt_text)        

    # with tab3:
    #     st.header("Edit Guidelines")
    #     st.subheader("Guidelines to Edit")

    #     # Selection for guideline type
    #     guideline_types = ["Brand Data", "Persona", "Platform Specs"]
    #     guidelines_type = st.selectbox("Select Guideline Type", [""] + guideline_types)

    #     if guidelines_type:
    #         # Convert guideline type to path-friendly format
    #         guideline_path = os.path.join(os.getcwd(), "data", guidelines_type.lower().replace(' ', '_'))
    #         guideline_files = os.listdir(guideline_path)
    #         selected_file = st.selectbox("Select File to Edit", [""] + guideline_files)

    #         if selected_file:
    #             file_path = os.path.join(guideline_path, selected_file)
    #             file_content = read_file(file_path)
    #             edited_content = st.text_area("Edit File", value=file_content, height=300)

    #             if edited_content != file_content:
    #                 if st.button(f"Save Changes to {selected_file}"):
    #                     write_file(file_path, edited_content)
                        
    # with tab4:
    #     st.header("Customer Profile Factory")
    #     # Load and edit existing personas
    #     customer_data_path = os.path.join(os.getcwd(), "data", "customer_data")
    #     persona_files = os.listdir(customer_data_path)
    #     persona_files_display = [f.replace('.json', '').replace('_', ' ').capitalize() for f in persona_files]
    #     selected_persona_file = st.selectbox("Select Persona File", [""] + persona_files_display)

    #     if selected_persona_file:
    #         file_path = os.path.join(customer_data_path, selected_persona_file.replace(' ', '_').lower() + '.json')
    #         persona_data = load_persona(file_path)
    #         persona_text = st.text_area("Edit Persona JSON", value=json.dumps(persona_data, indent=4), height=300)
    #         if persona_text != json.dumps(persona_data, indent=4):
    #             if st.button("Save Changes"):
    #                 save_persona(file_path, json.loads(persona_text))

    #     # Add a new persona
    #     st.button("Add New Persona", on_click=create_new_persona)

    #     # Display form to add a new persona if triggered
    #     if 'create_new' in st.session_state and st.session_state.create_new:
    #         new_persona = create_persona_form()
    #         if new_persona:
    #             new_persona_file = st.text_input("Enter new file name", value="new_persona.json")
    #             if st.button("Save New Customer Profile"):
    #                 with open(os.path.join(customer_data_path, new_persona_file), "w") as file:
    #                     json.dump(new_persona, file, indent=4)
    #                 del st.session_state.create_new  # Reset the creation state

# if __name__ == "__main__":
#     main()