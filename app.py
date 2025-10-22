from chart_type import ChartType

class App:
    def __init__(self):
        self.chartType = ChartType()

    def run(self):
        while True:
            query = input("Enter your query: ")

            if query == "stop":
                print("Programa finalizado")
                break  # Sai do loop

            self.chartType.set_chart_type(query)
        


if __name__ == "__main__":

    app = App()
    app.run()