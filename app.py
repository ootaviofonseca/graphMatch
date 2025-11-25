from chart_type import ChartType
from dataset_summary import DataSetSummary
from chart_generator import ChartGeneratorAgent

from tkinter import *
from tkinter import ttk, filedialog

# Global variables
file_path = ""
user_question = ""


class App:
    def __init__(self):
        self.path = None
        self.chartType = ChartType()
        self.dataSetSummary = None
        self.chartGeneratorAgent = ChartGeneratorAgent()

        # Creation of the main window for user interaction
        self.root = Tk()
        self.root.title("Chart Generator")
        self.frm = ttk.Frame(self.root, padding=10)
        self.frm.grid()

        # Label and text area for query
        ttk.Label(self.frm, text="Enter your query:").grid(column=0, row=0, sticky=W)
        self.txt_query = Text(self.frm, width=50, height=5)
        self.txt_query.grid(column=0, row=1, columnspan=2, pady=5)

        # Button to select CSV file
        ttk.Button(self.frm, text="Select CSV File", command=self.select_file).grid(column=0, row=2, pady=5)
        self.lbl_file = ttk.Label(self.frm, text="No file selected")
        self.lbl_file.grid(column=0, row=3, pady=5, sticky=W)

        # Button to run the query and generate chart
        ttk.Button(self.frm, text="Run Query", command=self.run_query).grid(column=0, row=4, pady=10)

        # Status label
        self.lbl_status = ttk.Label(self.frm, text="")
        self.lbl_status.grid(column=0, row=5, pady=5, sticky=W)

        # Quit button
        ttk.Button(self.frm, text="Quit", command=self.root.destroy).grid(column=0, row=6, pady=10)

    def select_file(self):
        """
        Opens a dialog box to select the CSV file
        """
        
        file_path = filedialog.askopenfilename(
            title="Select a CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.path = file_path
            self.lbl_file.config(text=f"Selected file: {self.path}")
            
            # Initialize dataset summary with selected file
            self.dataSetSummary = DataSetSummary(self.path)
        else:
            self.lbl_file.config(text="No file selected")

    # Function to run query
    def run_query(self):
        #Checks if the user selected a CSV file.
        if not self.path:
            self.lbl_status.config(text="Please select a CSV file first")
            return\
        
        #Retrieves the question and raises an error if it is missing
        query = self.txt_query.get("1.0", END).strip()
        if not query:
            self.lbl_status.config(text="Please enter a query")
            return

        #Select chat type and generate dataset summary
        chart_type = self.chartType.set_chart_type(query)
        df_summary = self.dataSetSummary.summarize()

        #Set a status message 
        self.lbl_status.config(text="Running chart generation...")
        self.root.update()

        #generate te chart
        final_code = self.chartGeneratorAgent.generate_and_test_code(chart_type, query, df_summary, self.path)

        self.lbl_status.config(text="Chart generation finished! Check 'resultsFolder'.")
        print("Query:", query)
        print("CSV Path:", self.path)
        print(final_code)

    # Run the Tkinter main loop
    def run(self):
        self.root.mainloop()



if __name__ == "__main__":

    app = App()
    app.run()