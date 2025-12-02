from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain.agents.middleware import ToolRetryMiddleware
import os
from dotenv import load_dotenv

import sys
@tool
def execute_code(code: str) -> str:
    """
    Execute Python code and return results
    """

    import subprocess
    import glob


    # Creates a command that runs Python and reads the code from the string
    process = subprocess.Popen(
        [sys.executable, "-c", code],  # The '-c'option allows passing code as a string
        stdout=subprocess.PIPE,   # Captures the output
        stderr=subprocess.PIPE,   # Captures errors
        text=True
    )

    #Waits for the process to finish and captures errors
    stdout , stderr = process.communicate()

    if process.returncode == 0:
        results_dir = os.path.abspath("results")
        svg_files = glob.glob(os.path.join(results_dir, "*.svg"))
        return {
            "ok": True,
            "path": max(svg_files, key=os.path.getmtime) if svg_files else None,
            "stdout": stdout
        }
    
    return {
        "ok": False,
        "error": stderr,
        "stdout": stdout
    }

# Function to create dynamic prompt based on chart type
def dynamic_prompt(chart_type, question: str, summary: str, path: str)-> str:

    base = (
            f"You must create a chart of type {chart_type}"
            f"If {chart_type} is empty, you must analyze the {question} and {summary} and determine which chart type should be used."
            f"If there is more than one option, create a weighting system to determine which chart type among the {chart_type} options makes the most sense with the {question}"
           
            f"This chart should answer the user’s question: {question}. "
            f"You are given a brief description of the dataframe: {summary}. This summary helps you understand how to organize the data for each chart type and which data to use for the charts."
            

            f"The names mentioned in the question may not exactly match the column names that exist in the dataset. "
            f"You must compare the names in the question with the dataset summary and determine which column(s) are most semantically related, even if the name is not an exact match. "
            f"You must always choose the column whose meaning best aligns with the user's query. "
            f"If multiple columns are possible matches, select the one with the highest semantic similarity according to the dataset summary. "
                        
            f"The code must follow the structure below. You should keep only the imports, the part where the CSV and its path are assigned, and the output format."
            f"The chart part is up to you, there’s an example code you may follow or not, but you must always adhere to Altair’s properties for each chart type.\n"
            f"Pay close attention to the format of the fields for each chart type to avoid creating a meaningless chart.\n"
            f"All charts must have a title"
            f"The agent is allowed to style the chart creatively in any way it finds interesting.\n\n"
            f"import altair as alt\n"
            f"import pandas as pd\n"
            f"import os\n"
            f"import uuid\n\n"
            f"path = r'{path}'\n"
            f"data = pd.read_csv(path)\n\n"
            )
    
    if len(chart_type) > 1:
        base += (
            f"# Create a chart\n"
            f"# You may adjust the encodings (like x, y, color, size, theta, etc.) "
            f"and other attributes as needed depending on the chart type."
            f"Select the most appropriate chart type for the question.\n\n"
            f"# Reference for chart marks (select only those necessary):\n"
            f"Arc -> mark_arc()         # A pie chart\n"
            f"Bar -> mark_bar()         # A bar plot\n"
            f"Line -> mark_line()       # A line plot\n"
            f"Scatter -> mark_circle()   # A scatter plot with filled circles (for scatter)\n"
            f"Boxplot -> mark_rect()       # Can be used for boxplot or heatmap\n\n"
            f"chart = alt.Chart(data).mark_<chart_type>().encode(\n"
            f"    # Adjust these encodings to match the dataset and selected chart type\n"
            f"    # Example: x='column_name:Q', y='column_name:N', color='category:N', theta='value:Q', etc.\n"
            f").properties(\n"
            f"    title='Your Chart Title Here'\n"
            f")\n\n"
        )
    elif chart_type[0]== "line":
        base += (
            f"# Create a line chart\n"
            f"chart = alt.Chart(data).mark_line().encode(\n"
            f"    x='x',       # can be changed to the column representing the x-axis\n"
            f"    y='f(x)',    # can be changed to the column representing the y-axis\n"
            f"    # Additional encodings can be added here, e.g., color='category:N', tooltip=['x','f(x)']\n"
            f").properties(\n"
            f"    title='Your Chart Title Here'  # Can change the title\n"
            f"    # Other properties can be added here, e.g., width=600, height=400\n"
            f")\n"
        )
    elif chart_type[0] == "bar":
        base += (f"# Create a bar chart with labels\n"
            f"base = alt.Chart(data).encode(\n"
            f"    x='<x_column>',     # Change to the column representing the x-axis values\n"
            f"    y='<y_column>:O',   # Change to the column representing the y-axis (ordinal) categories\n"
            f"    text='<text_column>' # Change to the column containing values to show on bars\n"
            f")\n"
            f"base.mark_bar() + base.mark_text(\n"
            f"    align='left',       # Can adjust alignment\n"
            f"    dx=2                # Can adjust offset\n"
            f")\n"
            f"# The agent can add additional encodings or properties as needed (e.g., color, tooltip, size, width, height)")
    elif chart_type[0] == "arc" :
        
        base += (
            f"# Create a pie chart\n"
            f"chart = alt.Chart(data).mark_arc().encode(\n"
            f"    theta='<value_column>',   # Change to the column representing the numeric values\n"
            f"    color='<category_column>' # Change to the column representing the categories\n"
            f"    # Additional encodings can be added here, e.g., tooltip=['<value_column>','<category_column>']\n"
            f")\n"
            f"# The agent can add additional properties as needed (e.g., innerRadius, sort, labels, width, height)"
        )
    elif chart_type[0] == "scatter":
        base += (
            f"# Create a scatter plot\n"
            f"chart = alt.Chart(data).mark_point().encode(\n"
            f"    x='<x_column>',          # Change to the column representing the x-axis values\n"
            f"    y='<y_column>',          # Change to the column representing the y-axis values\n"
            f"    color='<color_column>',  # Optional: column for color encoding\n"
            f"    size='<size_column>'     # Optional: column for size encoding\n"
            f"    # Additional encodings can be added here, e.g., tooltip=['<x_column>','<y_column>']\n"
            f")\n"
            f"# The agent can add additional properties as needed (e.g., shape, width, height, opacity)"

        )
    elif chart_type[0] == "boxplot":
        base += (
            f"# Create a boxplot\n"
            f"chart = alt.Chart(data).mark_boxplot().encode(\n"
            f"    x='<x_column>',          # Change to the column representing the categorical axis\n"
            f"    y='<y_column>',          # Change to the column representing the numeric values\n"
            f"    color='<color_column>'   # Optional: column for color encoding\n"
            f"    # Additional encodings can be added here, e.g., tooltip=['<x_column>','<y_column>']\n"
            f")\n"
            f"# The agent can add additional properties as needed (e.g., width, height, opacity, extent)"

        )

    base += (
        f"# Ensure the results folder exists and save the chart as SVG with a unique name\n"
        f"os.makedirs('results', exist_ok=True)\n"
        f"#Keep the format name"
        f"filename = f'results/chart_{{uuid.uuid4().hex}}.svg'\n"
        f"chart.save(filename)\n\n"
        f"The agent should NOT read any dataframe from the environment, just use the fixed path in the code." 
    )

    return base

class ChartGeneratorAgent:

    def __init__(self):
        # Load o .env
        load_dotenv()
        
        # Retrieves the key
        api_key = os.getenv("OPENAI_API_KEY")

        # If not found, returns an error
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")

        # Defining the model and creating the agent tat create the code
        self.model =  ChatOpenAI(model="gpt-4o-mini",  openai_api_key=api_key, temperature=0.3)
        self.code_generator = create_agent(
            system_prompt= (
                "You are a developer specialized in data visualization using Python and Altair."
            ),
            model=self.model,
        )

        #Agent that test and correct the code
        self.code_tester = create_agent(
            model=self.model,
            tools=[execute_code],
            middleware=[ # Middleware to retry on failure
                ToolRetryMiddleware(
                    max_retries=2,           # Tentar 2 vezes após erro
                    backoff_factor=2.0,      
                    initial_delay=1.0,       
                    on_failure="return_message"  # Envia o erro de volta ao agente
                )
            ],
            system_prompt= (
                "You receive Python code to execute. "
                "Use ONLY the execute_code tool to run the code. "
                
                "The tool ALWAYS returns a JSON object with fields: "
                "{ok: bool, path: str or null, error: str or null, stdout: str}. "

                "If ok == false, read the 'error' message, fix the code, and call execute_code again but DO NOT try more than 3 corrections. "
                "If after 3 attempts ok is still false, return the error message "
                "and stop correcting. "

                "If ok == true, return ONLY the value of 'path'."
            )
        )

        # Parser to standardize the output
        self.parser = StrOutputParser()

    def generate_code(self, chart_type, question: str, summary: str, path: str) -> str:
        
        # Create the dynamic prompt
        prompt = dynamic_prompt(chart_type, question, summary, path)
            
        result = self.code_generator.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })
 
        #Extract only the code part from the agent's response
        response = self.parser.invoke(result["messages"][-1])

        #Uncomment to see the generated code in terminal
        #print (response)
        return response
    
        
    def generate_and_test_code(self, chart_type, question: str, summary: str,  path: str ) -> str:
            """
            Full workflow: generate code → execute → correct if there is an error.
            """
            
            #Generate the code 
            code = self.generate_code(chart_type, question, summary, path)
            
            test_result = self.code_tester.invoke({
                "messages": [{"role": "user", "content": code}]
            })

            #Here we get the final output, which is either the SVG path or the error message after retries
            test_result["messages"][-1].content
            
            return self.parser.invoke(test_result["messages"][-1])

