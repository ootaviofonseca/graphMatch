import pandas as pd
import re


class DataSetSummary:
    # Keywords that usually indicate irrelevant/sensitive info
    # r"id", r"classid"
    sensitive_patterns = [
        r"user", r"login",
        r"email", r"phone", r"mobile", r"cpf", r"cnpj",
        r"address"
    ]

    def __init__(self, path: str):
        """Initialize the class with a CSV path."""
        self.path = path
        self.df = None
    
    def _ignore_sensitive_patterns(self, df):
        # Combine all patterns into one regex (case-insensitive)
        combined_pattern = re.compile("|".join(self.sensitive_patterns), re.IGNORECASE)

        safe_columns = [col for col in df.columns if not combined_pattern.search(col)]
    
        return df[safe_columns].dropna(how='all')
    
    
 
    def summarize(self):  
        self.df = pd.read_csv( self.path)
        self.df  = self._ignore_sensitive_patterns(self.df)

        colls_names = self.df.columns.values
        lines_num, colls_num = self.df.shape
        coll_types = self.df.dtypes

        summary = "The input dataframe has the following number of rows and columns: " + str(lines_num) + "x" + str(colls_num) + "\n" \
          "It has the following column names: " + str(colls_names) + "\n" \
          "And the data types for each column are: " + str(coll_types)

        print(summary)
        
        """print("Resumo do DataFrame")
        print("-" * 40)
        print(f"Linhas: {lines_num}")
        print(f"Colunas: {colls_num}")
        print("\nNome das colunas:")
        print(colls_names)
        print("\nTipos de colunas:")
        print(coll_types)
        """
        return summary

    
"""if __name__ == "__main__":
    path = "visEval_dataset/databases/activity_1/Student.csv"
    dataset_summary = DataSetSummary(path)
    #dataset_summary.csv_read(path)
    print( dataset_summary.summarize())"""