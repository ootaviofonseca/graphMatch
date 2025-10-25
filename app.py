from chart_type import ChartType
from dataset_summary import DataSetSummary
from chart_generator import charGeneratorAgent
class App:
    def __init__(self):
        path = "visEval_dataset/databases/activity_1/Student.csv"
        self.chartType = ChartType()
        self.dataSetSummary = DataSetSummary(path)
        self.chartGeneratorAgent = charGeneratorAgent()

    def run(self):
        while True:
            query = input("Enter your query: ")

            if query == "stop":
                print("Programa finalizado")
                break  # Sai do loop

            chart_type = self.chartType.set_chart_type(query)
            df_summary = self.dataSetSummary.summarize()
            fina_code = self.chartGeneratorAgent.generate(chart_type, query, df_summary )

            print(fina_code)

if __name__ == "__main__":

    app = App()
    app.run()