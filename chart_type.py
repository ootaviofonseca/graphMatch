# Terms related to Line Chart (Time Series)
line_terms = [
    "time", "year", "month", "day", "hour", "quarter", "date",
    "timeline", "evolution", "trend", "growth", "decline", "change over time",
    "historical", "progress", "time-based", "trend over time", "evolution over time",
    "history", "performance over time", "seasonal", "daily", "weekly", "monthly", "yearly",
    "trend analysis", "temporal analysis", "time pattern", "chronological",
    "data over time", "long-term change", "cumulative", "progression", "fluctuation",
    "increase", "decrease", "rise", "drop", "evolution chart", "temporal chart",
    "growth rate", "trend curve", "moving average", "rolling average",
    "timeline visualization", "sequential data", "chronological variation",
    "time sequence", "performance trend", "temporal trend", "rate over time",
    "time evolution", "progress trend", "yearly trend", "monthly change", "daily evolution",
    "growth pattern", "temporal progress", "trend line", "change trend"
]

# Terms related to Bar Chart (Comparison)
bar_terms = [
    "compare", "comparison", "difference", "vs", "versus", "contrast",
    "ranking", "top", "bottom", "worst", "best", "highest", "lowest",
    "by category", "by group", "by class", "by type", "by sector", "by region",
    "between categories", "between groups", "between products", "by city", "by gender",
    "quantity", "count", "number of", "frequency", "total", "volume",
    "performance comparison", "category analysis", "bar chart",
    "distribution per category", "category ranking", "count comparison",
    "metric comparison", "discrete data", "data by category",
    "absolute values", "relative values", "grouped comparison",
    "category-based", "value comparison", "ranking chart", "score comparison",
    "top performers", "best vs worst", "comparison by category",
    "ranking of", "sorted by", "ordered by", "category performance"
]

# Terms related to Pie Chart (Proportion/Quantity)
pie_terms = [
    "percentage", "proportion", "ratio", "share", "portion", "part of", "fraction",
    "composition", "distribution", "breakdown", "division", "segmentation",
    "participation", "contribution", "allocation", "part-to-whole", "relative share",
    "share of total", "percentage contribution", "market share", "sector share",
    "component distribution", "segment size", "slice", "section", "portion of total",
    "share analysis", "proportion chart", "percentage chart", "composition chart",
    "representativeness", "relative proportion", "proportional distribution",
    "split of", "distribution of total", "percent breakdown",
    "share distribution", "overall share", "pie chart", "share by category"
]

# Terms related to Scatter Plot (Relation/Association)
scatter_terms = [
    "correlation", "relationship", "relation between", "association",
    "dependence", "dependency", "link", "connection", "influence",
    "scatter", "x vs y", "y vs x", "dot plot", "scatter plot", "scatter diagram",
    "bivariate", "pairwise", "joint distribution", "joint variation",
    "linear relation", "nonlinear relation", "data pattern", "data clustering",
    "outlier", "anomaly", "variable interaction", "covariance", "co-variation",
    "correlation analysis", "relationship analysis", "scatter visualization",
    "point distribution", "data points", "pattern between variables",
    "relation chart", "relationship strength", "correlation trend",
    "regression", "correlation coefficient", "scatter comparison",
    "variable connection", "plot relationship", "data dispersion", "relationship plot", "plot against"
]

# Terms related to Boxplot (Distribution/Statistics)
boxplot_terms = [
    "median", "quartile", "first quartile", "third quartile",
    "minimum", "maximum", "range", "IQR", "interquartile range",
    "variability", "dispersion", "spread", "distribution", "data spread",
    "boxplot", "box-and-whisker", "box chart", "variance", "standard deviation",
    "statistical summary", "summary statistics", "data variability",
    "outlier", "extreme values", "whiskers", "distribution comparison",
    "spread analysis", "distribution overview", "data summary",
    "group comparison", "central tendency", "statistical distribution",
    "value distribution", "variance visualization", "quantile analysis",
    "comparative distribution", "spread between groups", "statistical boxplot"
]

# Terms to identify when there are explicit terms referencing the desired chart type
explicit_refs = {
    "line": [
        "line chart", "line graph", "line plot", "time series chart",
        "trend chart", "temporal chart", "evolution chart", "historical chart",
        "progress chart", "growth chart", "decline chart", "performance trend"
    ],
    "bar": [
        "bar chart", "bar graph", "bar plot", "column chart", "histogram",
        "comparison chart", "frequency chart", "ranking chart", "category chart",
        "value comparison chart", "grouped bar chart", "stacked bar chart"
    ],
    "arc": [
        "pie chart", "donut chart", "circle chart", "proportion chart",
        "percentage chart", "share chart", "composition chart", "segment chart",
        "part-to-whole chart", "breakdown chart", "relative share chart", "a pie", "pie"
    ],
    "scatter": [
        "scatter plot", "dot plot", "scatter diagram", "bivariate plot","scatter chart"
        "relationship chart", "correlation chart", "variable interaction chart",
        "data dispersion chart", "x vs y plot", "y vs x plot", "joint distribution chart"
    ],
    "boxplot": [
        "box plot", "boxplot", "box-and-whisker", "quartile chart",
        "distribution chart", "variance chart", "statistical summary chart",
        "data spread chart", "outlier chart", "interquartile range chart"
    ]
}

from pre_processing import PreProcessing
from rapidfuzz import process, fuzz
from nltk.util import ngrams
class ChartType:
    def __init__(self):
        pass

    def __explicit_reference(self, query):
        for chart, patterns in explicit_refs.items():
            for term in patterns:
                if term in query:
                    return chart  # tipo de gráfico explicitamente citado
        return None

    def __matching(self, token):
        """
        Checks the score and the possible corresponding chart for each token
        """
        # Performs matching for each type of chart
        results = {
            "line": process.extract(token, line_terms, scorer=fuzz.WRatio, limit=1),
            "bar": process.extract(token, bar_terms, scorer=fuzz.WRatio, limit=1),
            "arc": process.extract(token, pie_terms, scorer=fuzz.WRatio, limit=1),
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
        # Array containing the possible chart(s)
        perfect_matches = []

        # Performs preprocessing on the query and extracts the tokens
        preProcessor = PreProcessing()
        tokens = preProcessor.tokenizes(query)

        # When an explicit term is identified, it quickly selects the chart type
        explicit = self.__explicit_reference(preProcessor.query)
        if explicit:
            print(f"Explicit chart mention detected: {explicit.upper()}")
            perfect_matches.append(explicit)
            return perfect_matches

        # Creates bigrams and trigrams to improve the accuracy of chart predictions
        bigrams = [" ".join(gram) for gram in ngrams(tokens, 2)]
        trigrams = [" ".join(gram) for gram in ngrams(tokens, 3)]
        
        #remove irrelevant stopwords
        stopwords = ["of", "the", "a", "in", "and", "to", "for", "by","age"]
        tokens = [t for t in tokens if t not in stopwords]
        
        # Combines all the tokens
        all_tokens = tokens + bigrams + trigrams

        # Variables to represent the best score, chart, and the token
        best_score = 0
        best_chart = None
        best_token = None

        # Iterates through all tokens and checks their matches
        for token in all_tokens:
            atualMatch =  self.__matching(token)

            # Saves the current token score
            score = atualMatch["score"]
            
            # If the score is greater than 100, save it in perfect_matches (can exists more than one)
            if score == 100:
                perfect_matches.append(atualMatch["chart"])

            # Compares the score in each iteration with the highest one to find the best at the end
            if  score > best_score:               
                best_score = score
                best_chart = atualMatch["chart"]
                best_token = token
        
        #print(f"Melhor token: '{best_token}' → {best_chart.upper()} ({best_score}%)")
        
        if len(perfect_matches) > 1:
            print("\n Mais de um token com 100% de correspondência!")
            for match in perfect_matches:
                print(f" → CHART → {match.upper()}")
        
        # If there is no perfect match (100%), add the highest score to the array (> 85)
        if len(perfect_matches) == 0 and best_score > 85:
            perfect_matches.append( best_chart)
        
        print(f"Melhor token: {perfect_matches}")
        # Returns the match or matches
        return perfect_matches
        
        


           
    
        
        
        

        

        

