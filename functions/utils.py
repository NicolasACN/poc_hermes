import os
import json
from dotenv import find_dotenv, load_dotenv
import openai
# from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
# from langchain_core.pydantic_v1 import BaseModel, Field
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_openai.chat_models import ChatOpenAI
# from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from operator import itemgetter

import streamlit as st

#openai.api_key = st.secrets["OPENAI_API_KEY"]
load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# Instantiate GPT Model 
model = ChatOpenAI(model="gpt-4-turbo")

# DATA LOADING
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

retailer_product_data = {
    retailer: {
        lang: {
            product.capitalize().replace('_', ' ')[:-4]: open(os.path.join(DATA_FOLDER_PATH, "retailer_product_data", retailer, lang, product), "r").read() for product in os.listdir(os.path.join(DATA_FOLDER_PATH, "retailer_product_data", retailer, lang))
        } for lang in ["en", "fr"]
    } for retailer in os.listdir(os.path.join(DATA_FOLDER_PATH, "retailer_product_data"))
}
    

PROMPT_FOLDER_PATH = os.path.join(os.getcwd(), 'prompts')
assert os.path.exists(PROMPT_FOLDER_PATH)


def load_prompts(prompt_folder_path):
    with open(os.path.join(prompt_folder_path, "system_prompt.txt"), "r") as f:
        system_prompt = f.read()
    with open(os.path.join(prompt_folder_path, "human_prompt.txt"), "r") as f:
        human_prompt = f.read()
    return system_prompt, human_prompt

copywriting_system_prompt, copywriting_human_prompt = load_prompts(os.path.join(PROMPT_FOLDER_PATH, "Copywriting"))
brand_review_system_prompt, brand_review_human_prompt = load_prompts(os.path.join(PROMPT_FOLDER_PATH, "BrandReview"))
copywriting_review_system_prompt, copywriting_review_human_prompt = load_prompts(os.path.join(PROMPT_FOLDER_PATH, "CopywritingReview"))
tov_review_system_prompt, tov_review_human_prompt = load_prompts(os.path.join(PROMPT_FOLDER_PATH, "TOVReview"))
editor_system_prompt, editor_human_prompt = load_prompts(os.path.join(PROMPT_FOLDER_PATH, "Editor"))
role =  open(os.path.join(PROMPT_FOLDER_PATH, "Role", "role.txt"), "r").read()

# custom prompt
customization_system_prompt, customization_human_prompt = load_prompts(os.path.join(PROMPT_FOLDER_PATH, "Customization"))
edition_customization_system_prompt, edition_customization_human_prompt = load_prompts(os.path.join(PROMPT_FOLDER_PATH, "CustomizationEditor"))

def generate_pdp(product_name, product_details, language):
    # Output parser creation
    class Copywriting(BaseModel):
        generated_text: str = Field(description="The written product detail page.")

    class Feedback(BaseModel):
        feedback: str = Field(description="The feedback on the copy.")

    class Edition(BaseModel):
        edited_text: str = Field(description="The edited and improved version of the product detail page.")

    copywriting_output_parser = JsonOutputParser(pydantic_object=Copywriting)
    review_output_parser = JsonOutputParser(pydantic_object=Feedback)
    edition_output_parser = JsonOutputParser(pydantic_object=Edition)

    # Chains
    ## Copywriting
    copywriting_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(copywriting_system_prompt),
            HumanMessagePromptTemplate.from_template(copywriting_human_prompt)
        ],
        input_variables=["role", "persona", "language", "product_data", "brand_knowledge", "copywriting_guidelines", "platform_specs"],
        partial_variables={"format_instructions": copywriting_output_parser.get_format_instructions()}
    )

    copywriting_chain = copywriting_prompt | model | copywriting_output_parser

    ## Brand Review
    brand_review_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(brand_review_system_prompt),
            HumanMessagePromptTemplate.from_template(brand_review_human_prompt)
        ],
        input_variables=["role", "brand_knowledge", "generated_text"],
        partial_variables={"format_instructions": review_output_parser.get_format_instructions()}
    )
    brand_review_chain = brand_review_prompt | model | review_output_parser

    ## Copywriting Review
    copywriting_review_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(copywriting_review_system_prompt),
            HumanMessagePromptTemplate.from_template(copywriting_human_prompt)
        ],
        input_variables=["role", "copywriting_guidelines", "generated_text"],
        partial_variables={"format_instructions": review_output_parser.get_format_instructions()}
    )
    copywriting_review_chain = copywriting_review_prompt | model | review_output_parser

    ## TOV Review 
    def format_examples(example_dict):
        formated_text = ""
        for product in example_dict.keys():
            formated_text += str(product.upper()) + "\n"
            formated_text +=  str(example_dict[product]) + "\n"
            formated_text += "-" * 10 + "\n"
        return formated_text
            
    tov_review_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(tov_review_system_prompt),
            HumanMessagePromptTemplate.from_template(tov_review_human_prompt)
        ],
        input_variables=["role", "reference_examples", "generated_text"],
        partial_variables={"format_instructions": review_output_parser.get_format_instructions()}
    )
    tov_review_chain = tov_review_prompt | model | review_output_parser

    ## Edition
    edition_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(editor_system_prompt),
            HumanMessagePromptTemplate.from_template(editor_human_prompt)
        ],
        input_variables=["role", "perona", "generated_text", "feedback", "brand_knowledge", "copywriting_guidelines", "reference_examples", "platform_specs"], 
        partial_variables={"format_instructions": edition_output_parser.get_format_instructions()}
    )
    edition_chain = edition_prompt | model | edition_output_parser
    
    def format_feedback(reviews):
        brand_review, copywriting_review, tov_review = reviews
        return f"""Brand Feedback:
    {brand_review}

    Copywriting Feedback:
    {copywriting_review}

    Tone of Voice Feedback:
    {tov_review}

    """

    write_product_description_chain = (
        RunnablePassthrough.assign(generated_text=copywriting_chain)
        | RunnablePassthrough.assign(reference_examples=itemgetter("reference_examples") | RunnableLambda(format_examples))
        | RunnablePassthrough.assign(
            brand_review=brand_review_chain | itemgetter("feedback"),
            copywriting_review=copywriting_review_chain | itemgetter("feedback"),
            tov_review=tov_review_chain | itemgetter("feedback")
        ) | RunnablePassthrough.assign(feedback=itemgetter("brand_review", "copywriting_review", "tov_review") | RunnableLambda(format_feedback))
        | RunnablePassthrough.assign(edited_text=edition_chain | itemgetter("edited_text"))
        | itemgetter("edited_text")
    )   
    
    if product_name in product_data[language]:
        product_details = product_data[language][product_name]
    else:
        def format_product_details(product_detail_list):
            return  f"PRODUCT DESCRIPTION:\n{product_detail_list[0]}\n\nOBJECT DESCRIPTION:\n{product_detail_list[1]}\n\nADDITIONAL INFO:\n{product_detail_list[2]}"
        product_details = format_product_details(product_details)

            
    return write_product_description_chain.invoke({
        "role": role, 
        "persona": persona, 
        "language": language,
        "product_name": product_name,
        "product_data": product_details,
        "brand_knowledge": brand_knowledge,
        "copywriting_guidelines": copywriting_guidelines,
        "reference_examples": product_data[language],
        "platform_specs": hermes_specs,   
        "existing_product_dp": product_data[language][product_name] 
    })
    
def format_pdp_text(pdp_text):
    # Split the input text by double newlines to separate the paragraphs
    paragraphs = pdp_text.strip().split("\n\n")
    
    # Initialize an empty list to hold the formatted paragraphs
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        # Split each paragraph by the first newline to separate the title from the content
        lines = paragraph.split("\n", 1)  # Only split on the first newline
        title = lines[0].strip()  # First line is the title
        
        # Check if there is any content after the title
        content = lines[1].strip() if len(lines) > 1 else ""

        # Format the title in bold with a line break if there is content
        if title != "---":
            formatted_paragraph = f"**{title}**"
        else:
            formatted_paragraph = title
        if content:
            formatted_paragraph += f"  \n{content}"
        
        formatted_paragraphs.append(formatted_paragraph)
    
    # Join the formatted paragraphs with double newlines
    formatted_text = "\n\n".join(formatted_paragraphs)
    
    return formatted_text

def load_product_details(product_name, language):
    product_name = product_name.lower().replace(' ', '_').replace('è', 'e')
    if not ".txt" in product_name:
        product_name += ".txt"
        
    with open(os.path.join(os.getcwd(), "data", "product_details", language, "product_description", product_name), 'r') as f:
        product_description = f.read()
    with open(os.path.join(os.getcwd(), "data", "product_details", language, "object_description", product_name), 'r') as f:
        object_description = f.read()
    with open(os.path.join(os.getcwd(), "data", "product_details", language, "additional_info", product_name), 'r') as f:
        additional_info = f.read()
    return product_description, object_description, additional_info

def format_product_details(product_description, object_description, additional_info):
    return f"PRODUCT DESCRIPTION:\n{product_description}\n\nOBJECT DESCRIPTION:\n{object_description}\n\nADDITIONAL INFO:\n{additional_info}\n\n"

def retailer_customize_pdp(product_name, language): 
    # Output parser creation
    class Customization(BaseModel):
        customized_text: str = Field(description="The retailer customized product detail page.")

    class Feedback(BaseModel):
        feedback: str = Field(description="The feedback on the copy.")

    class Edition(BaseModel):
        edited_text: str = Field(description="The edited and improved version of the customized product detail page.")

    customization_output_parser = JsonOutputParser(pydantic_object=Customization)
    review_output_parser = JsonOutputParser(pydantic_object=Feedback)
    edition_output_parser = JsonOutputParser(pydantic_object=Edition)

    # Chains
    ## Copywriting
    customization_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(customization_system_prompt),
            HumanMessagePromptTemplate.from_template(customization_human_prompt)
        ],
        input_variables=["role", "persona", "language", "existing_product_dp", "brand_knowledge", "copywriting_guidelines", "reference_examples", "platform_specs"],
        partial_variables={"format_instructions": customization_output_parser.get_format_instructions()}
    )

    customization_chain = customization_prompt | model | customization_output_parser

    ## Brand Review
    brand_review_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(brand_review_system_prompt),
            HumanMessagePromptTemplate.from_template(brand_review_human_prompt)
        ],
        input_variables=["role", "brand_knowledge", "generated_text"],
        partial_variables={"format_instructions": review_output_parser.get_format_instructions()}
    )
    brand_review_chain = brand_review_prompt | model | review_output_parser

    ## Copywriting Review
    copywriting_review_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(copywriting_review_system_prompt),
            HumanMessagePromptTemplate.from_template(copywriting_human_prompt)
        ],
        input_variables=["role", "copywriting_guidelines", "generated_text"],
        partial_variables={"format_instructions": review_output_parser.get_format_instructions()}
    )
    copywriting_review_chain = copywriting_review_prompt | model | review_output_parser

        ## TOV & Platform Specs Review 
    def format_examples(example_dict):
        formated_text = ""
        for language in ["en", "fr"]:
            formated_text += f"\nLanguage: {language}\n\n"
            for product in example_dict["hermes"][language]:
                formated_text += f"Original text:\n{example_dict['hermes'][language][product]}\n\nAdapted text:\n{example_dict['sephora'][language][product]}\n\n"
        return formated_text
            
    tov_review_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(tov_review_system_prompt),
            HumanMessagePromptTemplate.from_template(tov_review_human_prompt)
        ],
        input_variables=["role", "reference_examples", "generated_text"],
        partial_variables={"format_instructions": review_output_parser.get_format_instructions()}
    )
    tov_review_chain = tov_review_prompt | model | review_output_parser

    ## Edition
    edition_customization_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(edition_customization_system_prompt),
            HumanMessagePromptTemplate.from_template(edition_customization_human_prompt)
        ],
        input_variables=["role", "persona", "generated_text", "feedback", "brand_knowledge", "copywriting_guidelines", "reference_examples", "existing_product_dp", "platform_specs"], 
        partial_variables={"format_instructions": edition_output_parser.get_format_instructions()}
    )
    edition_customization_chain = edition_customization_prompt | model | edition_output_parser

    def format_feedback(reviews):
        brand_review, copywriting_review, tov_review = reviews
        return f"""Brand Feedback:
    {brand_review}

    Copywriting Feedback:
    {copywriting_review}

    Tone of Voice and Platform specs compliance Feedback:
    {tov_review}

    """

    customize_product_description_chain = (
        RunnablePassthrough.assign(generated_text=customization_chain)
        | RunnablePassthrough.assign(reference_examples=itemgetter("reference_examples") | RunnableLambda(format_examples))
        | RunnablePassthrough.assign(
            brand_review=brand_review_chain | itemgetter("feedback"),
            copywriting_review=copywriting_review_chain | itemgetter("feedback"),
            tov_review=tov_review_chain | itemgetter("feedback")
        ) | RunnablePassthrough.assign(feedback=itemgetter("brand_review", "copywriting_review", "tov_review") | RunnableLambda(format_feedback))
        | RunnablePassthrough.assign(edited_text=edition_customization_chain | itemgetter('edited_text'))
        | itemgetter("edited_text")
    )   
    if product_name in product_data[language]:
        product_details = product_data[language][product_name]
    else:
        def format_product_details(product_detail_list):
            return  f"PRODUCT DESCRIPTION:\n{product_detail_list[0]}\n\nOBJECT DESCRIPTION:\n{product_detail_list[1]}\n\nADDITIONAL INFO:\n{product_detail_list[2]}"
        product_details = format_product_details(product_details)

    customize_product_description_chain.invoke({
        "role": role, 
        "persona": persona, 
        "language": language,
        "product_name": product_name,
        "brand_knowledge": brand_knowledge,
        "copywriting_guidelines": copywriting_guidelines,
        "reference_examples": retailer_product_data,
        "platform_specs": sephora_specs,   
        "existing_product_dp": product_data[language]["Terre d Hermès"], 
        "product_data": retailer_product_data["sephora"][language]["Terre d hermes"] 
    })
    
    return customize_product_description_chain.invoke({
        "role": role, 
        "persona": persona, 
        "language": language,
        "product_name": product_name,
        "product_data": product_details,
        "brand_knowledge": brand_knowledge,
        "copywriting_guidelines": copywriting_guidelines,
        "reference_examples": retailer_product_data,
        "platform_specs": sephora_specs,   
        "existing_product_dp": product_data[language][product_name] 
    })
