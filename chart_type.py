# Terms related to Line Chart (Time Series)
line_terms = [
    "time", "year", "month", "day", "hour", "quarter",
    "evolution", "trend", "growth", "decline", "variation",
    "history", "time series", "progress", "changes over time",
    "fluctuation", "temporal pattern", "curve", "trend line",
    "performance over time", "monthly progress", "increase/decrease", "line chart"
]

# Terms related to Bar Chart (Comparison)
bar_terms = [
    "compare", "difference", "vs", "contrast",
    "ranking", "top", "worst", "best",
    "by category", "by group", "between sectors", "between products",
    "quantity", "absolute values", "frequency",
    "performance comparison", "category analysis", "column chart",
    "variation between groups", "metric contrast", "bar chart"
]

# Terms related to Pie Chart (Proportion/Quantity)
pie_terms = [
    "percentage", "proportion", "part of", "fraction",
    "participation", "share", "distribution", "division",
    "segment", "slice", "composition", "market share",
    "total division", "representativeness", "relative participation",
    "contribution of each item", "market proportion", "pie chart"
]

# Terms related to Scatter Plot (Relation/Association)
scatter_terms = [
    "correlation", "relationship between", "association",
    "dispersion", "x vs y", "scatter plot", "dot plot",
    "dependency", "trend between variables", "linear relation",
    "joint distribution", "joint variation", "data pattern",
    "data clustering", "outlier", "relation analysis"
]

# Terms related to Boxplot (Distribution/Statistics)
boxplot_terms = [
    "median", "quartile", "outlier", "variability",
    "minimum", "maximum", "first quartile", "third quartile",
    "distribution", "spread", "range",
    "group comparison", "data spread", "box-and-whisker",
    "statistical summary", "summarized data", "outlier visualization", "boxplot"
]

from pre_processing import PreProcessing
from rapidfuzz import process, fuzz

class ChartType:

    def __matching(self, token):
        """
        Checks the score and the possible corresponding chart for each token
        """
        # Performs matching for each type of chart
        results = {
            "line": process.extract(token, line_terms, scorer=fuzz.WRatio, limit=1),
            "bar": process.extract(token, bar_terms, scorer=fuzz.WRatio, limit=1),
            "pie": process.extract(token, pie_terms, scorer=fuzz.WRatio, limit=1),
            "scatter": process.extract(token, scatter_terms, scorer=fuzz.WRatio, limit=1),
            "boxplot": process.extract(token, boxplot_terms, scorer=fuzz.WRatio, limit=1)
        }

        #Extracts only the score from each result.
        scores = {chart: result[0][1] if result else 0 for chart, result in results.items()}

        # Gets the chart with the highest score
        best_chart = max(scores, key=scores.get)
        best_score = scores[best_chart]

        #Structure the information
        token_record = {
            "score": best_score,
            "chart": best_chart
        }

        return token_record

    def set_chart_type(self, query):
        """
        Finds the best chart type or the possible top options (if more than one option is needed as a result)
        """

        # Performs preprocessing on the query and extracts the tokens
        preProcessor = PreProcessing()
        tokens = preProcessor.tokenizes(query)
        
        # Variables to represent the best score, chart, and the token
        best_score = 0
        best_chart = None
        best_token = None

        # Array containing the possible chart(s)
        perfect_matches = []

        # Iterates through all tokens and checks their matches
        for token in tokens:
            atualMatch =  self.__matching(token)

            # Saves the current token score
            score = atualMatch["score"]
            
            # If the score is greater than 100, save it in perfect_matches (can exists more than one)
            if score == 100:
                perfect_matches.append({"token": token, "chart":  atualMatch["chart"]})

            # Compares the score in each iteration with the highest one to find the best at the end
            if  score > best_score:               
                best_score = score
                best_chart = atualMatch["chart"]
                best_token = token
        
        print(f"✅ Melhor token: '{best_token}' → {best_chart.upper()} ({best_score}%)")
        

        if len(perfect_matches) > 1:
            print("\n⚠️ Mais de um token com 100% de correspondência!")
            for match in perfect_matches:
                print(f" → Token '{match['token']}' → {match['chart'].upper()}")
        
        # If there is no perfect match (100%), add the highest score to the array
        if len(perfect_matches) == 0:
            perfect_matches.append({"token": best_token, "chart": best_chart})
        
        # Returns the match or matches
        return perfect_matches
        
        


           
    
        
        
        

        

        

