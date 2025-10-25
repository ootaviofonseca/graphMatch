from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser

import os

from dotenv import load_dotenv


"""import threading
def run_code(code_str):
    Execute code in a thread; returns success or error

    result = {"status": None}  # container simples para pegar resultado da thread

    def _execute():
        try:
            exec(code_str, {})  # executa de forma isolada
            result["status"] = "Success"
        except Exception as e:
            result["status"] = f"Error: {e}"

    thread = threading.Thread(target=_execute)
    thread.start()
    thread.join()  # se quiser async, pode remover
    return result["status"]"""




class charGeneratorAgent:

    def __init__(self):
        # Load o .env
        load_dotenv()
        # Retrieves the key
        api_key = os.getenv("OPENAI_API_KEY")

        # If not found, returns an error
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")

        # Defining the model and creating the agent
        self.model =  ChatOpenAI(model="gpt-3.5-turbo",  openai_api_key=api_key)
        self.agent = create_agent(
            model=self.model,
            #tools=[run_code]
        )

        # Parser to standardize the output
        self.parser = StrOutputParser()

    def generate(self, chart_type, question, summary):
        
        prompt = (
            f"You are a coding assistant specialized in data visualization using Altair. "
            f"Generate only the Python code that creates an Altair chart of type {chart_type} "
            f"that answers the user’s question: {question}. "
            f"You are given a brief description of the dataframe: {summary}. "
            f"The generated code must follow this format (values, columns, and chart type can vary, but keep the structure):\n\n"
            f"import altair as alt\n"
            f"import pandas as pd\n"
            f"import vl_convert as vlc\n\n"
            f"path = 'visEval_dataset/databases/activity_1/Student.csv'\n"
            f"data = pd.read_csv(path)\n\n"
            f"# Create a chart\n"
            f"chart = alt.Chart(data).mark_<chart_type>().encode(\n"
            f"    x='<x_column>:<type>',\n"
            f"    y='<y_column>:<type>',\n"
            f").properties(\n"
            f"    title='<chart_title>'\n"
            f")\n\n"
            f"# Convert the chart to PNG\n"
            f"png_bytes = vlc.vegalite_to_png(chart.to_dict())\n\n"
            f"# Save the PNG file\n"
            f"with open('grafico.png', 'wb') as f:\n"
            f"    f.write(png_bytes)\n\n"
            f"The agent should NOT read any dataframe from the environment; "
            f"just use the fixed path in the code. "
            f"The structure of the chart may change depending on the chart type, but the path, imports, chart object, and PNG export must always remain."
          )

        result = self.agent.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })

        response = self.parser.invoke(result["messages"][-1])

        return response


# Definir as 2 tools
"""@tool
def resumo(a: int, b: int) -> int:
    
    return a + b

@tool
def multiplicar(a: int, b: int) -> int:
    return a * b

# Criar o agent
model = ChatOpenAI(model="gpt-4o-mini")
agent = create_agent(
    model=model,
    tools=[somar, multiplicar]
)"""


