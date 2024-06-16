from functions.utils import personalize_content, write_file, read_file, create_persona_form, create_new_persona, save_persona, load_persona
import streamlit as st
import os
import json

# Define the product options based on the categories
product_options = {
    "fragrance": [
        "Chance Eau de Parfum Spray",
        "Chance Eau de Toilette Spray",
        "Chance Hair Mist",
        "Coco Mademoiselle Eau de Parfum Spray",
        "Coco Mademoiselle Eau de Toilette Spray",
        "Cristale Eau de Parfum Spray",
        "Gabrielle Chanel Essence Eau de Parfum Spray",
        "N°5 Eau de Parfum Spray",
        "N°5 Extrait Bottle",
        "N°5 Eau Premiere Spray",
        "N°19 Eau de Parfum Spray"
    ],
    "skincare": [
        "N°1 de Chanel Lip and Cheek Balm",
        "N°1 de Chanel Powder-to-Foam Cleanser",
        "N°1 de Chanel Revitalizing Cream",
        "N°1 de Chanel Revitalizing Foundation",
        "N°1 de Chanel Revitalizing Serum",
        "N°1 de Chanel Skin Enhancer"
    ]
}

# Define the app layout and functionality
def main():
    st.title("Product Description Personalization")
    tab1, tab2, tab3, tab4 = st.tabs(["Product Description Personalization", "Prompt Factory", "Edit Guidelines", "Customer Profile Factory"])

    with tab1: 
        # Product Selection
        st.header("Product")
        product_category = st.selectbox("Product Category", options=["", "fragrance", "skincare"])
        product_name = None
        if product_category:
            product_name = st.selectbox("Product Name", options=[""] + product_options[product_category])

        # Customer Profile Selection
        st.header("Customer Profile")
        customer_data_path = os.path.join(os.getcwd(), "data", "customer_data")
        customer_files = os.listdir(customer_data_path)
        customer_profiles = [f.replace('.json', '').replace('_', ' ').capitalize() for f in customer_files]
        customer_profile_name = st.selectbox("Select Customer Profile", options=[""] + customer_profiles)

        # Load customer profile data
        customer_profile = {}
        if customer_profile_name:
            with open(os.path.join(customer_data_path, customer_profile_name.replace(' ', '_').lower() + '.json')) as f:
                customer_profile = json.load(f)

        # Target Platform Selection
        st.header("Target Platform")
        platform_data_path = os.path.join(os.getcwd(), "data", "platform_specs")
        platform_files = os.listdir(platform_data_path)
        platform_names = [f.replace('.txt', '').replace('_', ' ').capitalize() for f in platform_files]
        platform_name = st.selectbox("Select Target Platform", options=[""] + platform_names)

        # Personalize Content
        st.header("Personalize Content")
        if st.button("Generate Personalized Description"):
            personalized_text = personalize_content(product_category, product_name, customer_profile, platform_name)
            st.write(personalized_text)
            
    with tab2:
            st.header("Edit Prompts")
            # Select a folder
            prompt_base_path = os.path.join(os.getcwd(), "prompts")
            folders = os.listdir(prompt_base_path)
            prompt_folder = st.selectbox("Select a folder", [""] + folders)

            if prompt_folder:
                # System Prompt editing
                st.subheader("System Prompt")
                system_prompt_path = os.path.join(prompt_base_path, prompt_folder, "system_prompt.txt")
                system_prompt_content = read_file(system_prompt_path)
                system_prompt_text = st.text_area("System Prompt", value=system_prompt_content, height=300)
                if system_prompt_text != system_prompt_content:
                    if st.button("Save System Prompt"):
                        write_file(system_prompt_path, system_prompt_text)

                # Human Prompt editing
                st.subheader("Human Prompt")
                human_prompt_path = os.path.join(prompt_base_path, prompt_folder, "human_prompt.txt")
                human_prompt_content = read_file(human_prompt_path)
                human_prompt_text = st.text_area("Human Prompt", value=human_prompt_content, height=300)
                if human_prompt_text != human_prompt_content:
                    if st.button("Save Human Prompt"):
                        write_file(human_prompt_path, human_prompt_text)        

    with tab3:
        st.header("Edit Guidelines")
        st.subheader("Guidelines to Edit")

        # Selection for guideline type
        guideline_types = ["Brand Data", "Persona", "Platform Specs"]
        guidelines_type = st.selectbox("Select Guideline Type", [""] + guideline_types)

        if guidelines_type:
            # Convert guideline type to path-friendly format
            guideline_path = os.path.join(os.getcwd(), "data", guidelines_type.lower().replace(' ', '_'))
            guideline_files = os.listdir(guideline_path)
            selected_file = st.selectbox("Select File to Edit", [""] + guideline_files)

            if selected_file:
                file_path = os.path.join(guideline_path, selected_file)
                file_content = read_file(file_path)
                edited_content = st.text_area("Edit File", value=file_content, height=300)

                if edited_content != file_content:
                    if st.button(f"Save Changes to {selected_file}"):
                        write_file(file_path, edited_content)
                        
    with tab4:
        st.header("Customer Profile Factory")
        # Load and edit existing personas
        customer_data_path = os.path.join(os.getcwd(), "data", "customer_data")
        persona_files = os.listdir(customer_data_path)
        persona_files_display = [f.replace('.json', '').replace('_', ' ').capitalize() for f in persona_files]
        selected_persona_file = st.selectbox("Select Persona File", [""] + persona_files_display)

        if selected_persona_file:
            file_path = os.path.join(customer_data_path, selected_persona_file.replace(' ', '_').lower() + '.json')
            persona_data = load_persona(file_path)
            persona_text = st.text_area("Edit Persona JSON", value=json.dumps(persona_data, indent=4), height=300)
            if persona_text != json.dumps(persona_data, indent=4):
                if st.button("Save Changes"):
                    save_persona(file_path, json.loads(persona_text))

        # Add a new persona
        st.button("Add New Persona", on_click=create_new_persona)

        # Display form to add a new persona if triggered
        if 'create_new' in st.session_state and st.session_state.create_new:
            new_persona = create_persona_form()
            if new_persona:
                new_persona_file = st.text_input("Enter new file name", value="new_persona.json")
                if st.button("Save New Customer Profile"):
                    with open(os.path.join(customer_data_path, new_persona_file), "w") as file:
                        json.dump(new_persona, file, indent=4)
                    del st.session_state.create_new  # Reset the creation state

if __name__ == "__main__":
    main()