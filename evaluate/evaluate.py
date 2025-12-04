

import glob
import os
import re
import time
import uuid
import json
import random
import shutil
import csv
from collections import defaultdict
from datetime import datetime

# Import agests and utilities
from chart_generator import ChartGeneratorAgent
#from chart_generator_gemini import ChartGeneratorAgent
from chart_type import ChartType
from dataset_summary import DataSetSummary

import xml.etree.ElementTree as ET

# Diretórios
RESULTS_DIR = os.path.abspath("results")
LOGS_DIR = os.path.abspath("logs")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)



# Configurations
QNT_QUERIES_LIMIT = 1150   # global limit of queries to process
SVG_WAIT_TIMEOUT = 6.0     # wait timeout for SVG generation
SVG_POLL_INTERVAL = 0.12   # polling interval to check for new SVGs
SHUFFLE_QUERIES = True     # shuffle queries globally

def wait_for_svg(timeout=SVG_WAIT_TIMEOUT, poll_interval=SVG_POLL_INTERVAL):
    """
    Waits up to 'timeout' seconds for at least one .svg file to appear in RESULTS_DIR.
    Returns the path of the newest file or None if timeout.
    """
    start = time.time()
    last_seen = None
    while time.time() - start < timeout:
        svg_files = glob.glob(os.path.join(RESULTS_DIR, "*.svg"))
        if svg_files:
            novo = max(svg_files, key=os.path.getmtime)
            # return only if it's a new file
            if novo != last_seen:
                return novo
        time.sleep(poll_interval)
    return None

def extract_texts_svg(svg_path):
    """
    Extracts visible texts from an SVG. Fallback: also returns raw content for searches.
    Returns: list_of_texts, raw_content
    """
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        texts = []
        for elem in root.iter():
            # direct text
            if elem.text and elem.text.strip():
                texts.append(elem.text.strip())
            # also get text from attributes that often hold labels
            for attr in ("aria-label", "title", "data-label", "label"):
                if elem.get(attr):
                    texts.append(elem.get(attr).strip())
        with open(svg_path, "r", encoding="utf-8") as f:
            raw = f.read()
        return texts, raw
    except Exception:
        # fallback: devolver conteúdo bruto
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                raw = f.read()
            # tentar extrair textos simples por regex de tags <text>...</text>
            texts = re.findall(r"<text[^>]*>(.*?)</text>", raw, flags=re.DOTALL)
            texts = [re.sub(r"\s+", " ", t).strip() for t in texts if t.strip()]
            return texts, raw
        except Exception:
            return [], ""

def save_csv(path, rows, header):
    """Saves a list of dicts/tuples to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in rows:
            writer.writerow(r)


import re
from bs4 import BeautifulSoup

def extract_svg_points(svg_content: str):
    """
    Extracts the number of points (marks) from the SVG.
    Works for scatter, line, area, bar with transformations.
    """
    soup = BeautifulSoup(svg_content, 'xml')

    # circle points
    circles = soup.find_all("circle")

    # path markers (line charts)
    paths = soup.find_all("path")
    path_points = 0
    for p in paths:
        d = p.get("d", "")
        # count 'M' or 'L' commands that represent points
        matches = re.findall(r"[ML]\s*([\d\.]+),([\d\.]+)", d)
        path_points += len(matches)

    # rect (bar chart)
    rects = soup.find_all("rect")
    rect_points = 0
    for r in rects:
        if r.get("width") and r.get("height"):
            # ignore background
            if not (r.get("width") == "944" or r.get("height") == "464"):
                rect_points += 1

    total = len(circles) + path_points + rect_points
    return total


def validate_svg_with_data(svg_content: str, x_data):
    """
    Validates by comparing the number of points.
    """
    total_data = len(x_data)
    total_svg = extract_svg_points(svg_content)

    return total_data == total_svg


def extract_numbers(data, agent: ChartGeneratorAgent, limit=QNT_QUERIES_LIMIT):
    """
    Main function corrected and improved.
    data: dict (content of visEval_single.json)ChartGeneratorAgent
    agent: instance of ChartGeneratorAgent
    limit: limit of queries to process (global)
    """

    # metrics
    contFound = 0
    contNotFound = 0
    contQuery = 0
    correctCharts = 0
    fails = 0
    times = []

    errors = []
    chartType = ChartType()
    hardness_levels = defaultdict(lambda: {'correct': 0, 'incorrect': 0})

    # PREPARE list of (key, value, query) to shuffle
    all_items = []
    for key, value in data.items():
        nl_queries = value.get("nl_queries", [])
        for q in nl_queries:
            all_items.append((key, value, q))

    if SHUFFLE_QUERIES:
        random.shuffle(all_items)

    # If the user requested a smaller limit
    all_items = all_items[:limit]

    # CSV log per query
    query_logs = []
    # rows: key, query, found (0/1), reason, svg_name, elapsed, hardness, chart_expected

    for (key, value, query) in all_items:
        if contQuery >= limit:
            break

        contQuery += 1

        db_id = value["db_id"]
        csv_id = value["vis_query"]["data_part"]["sql_part"]
        # expected values (from JSON)
        chart_expected = value["vis_obj"]["chart"][0]
        x_data = value["vis_obj"]["x_data"][0]
        y_data = value["vis_obj"]["y_data"][0]
        hardness = value.get("hardness", "unknown")

        # get table from SQL (safe)
        match = re.search(r'(?i)FROM\s+([A-Za-z_][A-Za-z0-9_]*)', csv_id)
        if not match:
            errors.append(f"[{key}] No table found in SQL: {csv_id}")
            # log and continue
            query_logs.append((key, query, 0, "no_table_in_sql", "", 0.0, hardness, chart_expected, ""))
            contNotFound += 1
            hardness_levels[hardness]['incorrect'] += 1
            continue
        tabela = match.group(1)
        dataset_path = os.path.join("visEval_dataset", "databases", db_id, f"{tabela}.csv")
        if not os.path.exists(dataset_path):
            errors.append(f"[{key}] CSV file not found: {dataset_path}")
            query_logs.append((key, query, 0, "csv_not_found", "", 0.0, hardness, chart_expected, ""))
            contNotFound += 1
            hardness_levels[hardness]['incorrect'] += 1
            continue

        dataset_summary = DataSetSummary(dataset_path).summarize()

        # identify chart_type suggested by your module (can return list/string)
        chart_predicted = chartType.set_chart_type(query)

        # count "chart expected" only based on proper semantic comparison:
        if isinstance(chart_predicted, (list, tuple, set)):
            chart_predicted_str = ",".join(map(str, chart_predicted))
        else:
            chart_predicted_str = str(chart_predicted)

        if chart_expected and chart_expected in chart_predicted_str:
            correctCharts += 1

        start_t = time.time()
        try:
            #call to agent
            agent.generate_and_test_code(chart_predicted, query, dataset_summary, dataset_path)
        except Exception as e:
            elapsed = time.time() - start_t
            fails += 1
            errors.append(f"[{key}] Error generating (agent): {e}")
            query_logs.append((key, query, 0, f"agent_error: {e}", "", round(elapsed, 3), hardness, chart_expected, chart_predicted_str))
            contNotFound += 1
            hardness_levels[hardness]['incorrect'] += 1
            times.append(elapsed)
            continue

        # Wait for the newly created SVG
        latest_svg = wait_for_svg(timeout=SVG_WAIT_TIMEOUT)
        elapsed = time.time() - start_t
        times.append(elapsed)

        if not latest_svg:
            fails += 1
            errors.append(f"[{key}] Timeout waiting for SVG for query (elapsed={elapsed:.2f}s).")
            query_logs.append((key, query, 0, "svg_timeout", "", round(elapsed, 3), hardness, chart_expected, chart_predicted_str))
            contNotFound += 1
            hardness_levels[hardness]['incorrect'] += 1
            continue

        # extract texts and raw
        svg_texts, svg_raw = extract_texts_svg(latest_svg)

        # Simple normalization: lower-case strings of texts
        svg_texts_norm = [str(t).lower() for t in svg_texts]
        svg_raw_lower = svg_raw.lower()

        # Robust checks:
        def contains_all_values(values, texts_norm, raw_lower):
            # Check if ALL values exist somewhere (extracted text or raw)
            for v in values:
                sv = str(v).strip().lower()
                if not sv:
                    return False
                if sv in texts_norm:
                    continue
                # look for exact word in raw (or substring)
                if sv in raw_lower:
                    continue
                # try token match: e.g. "2010" in "2010\n"
                found_token = False
                for t in texts_norm:
                    if sv in t:
                        found_token = True
                        break
                if not found_token:
                    return False
            return True

        found_x = contains_all_values(x_data, svg_texts_norm, svg_raw_lower)
        found_y = contains_all_values(y_data, svg_texts_norm, svg_raw_lower)

        found = bool(found_x and found_y)

        if found:
            contFound += 1
            hardness_levels[hardness]['correct'] += 1
            reason = "found_x_and_y"
        else:
            found = validate_svg_with_data(svg_raw, x_data)
            if found:
                contFound += 1
                hardness_levels[hardness]['correct'] += 1
                reason = "found_by_point_count"
            else:
                contNotFound += 1
                hardness_levels[hardness]['incorrect'] += 1
                # major detail on why it was not found:
                if not found_x and not found_y:
                    reason = "missing_x_and_y"
                elif not found_x:
                    reason = "missing_x"
                else:
                    reason = "missing_y"

        # save log per query
        svg_name = os.path.basename(latest_svg) if latest_svg else ""
        query_logs.append((key, query, int(found), reason, svg_name, round(elapsed, 3), hardness, chart_expected, chart_predicted_str))

        # optional: move/rename the svg to include key/idx (not mandatory)
        try:
            # generate stable name for inspection
            stable_name = f"chart_{key}_{contQuery}_{uuid.uuid4().hex[:6]}.svg"
            stable_path = os.path.join(RESULTS_DIR, stable_name)
            shutil.move(latest_svg, stable_path)
        except Exception:
            stable_path = latest_svg



    #  Summary 
    total = contQuery
    found = contFound
    not_found = contNotFound
    fail_count = fails
    avg_time = (sum(times) / len(times)) if times else 0.0
    success_rate = (found / total * 100) if total > 0 else 0.0

    # save logs CSV
    query_logs_path = os.path.join(LOGS_DIR, "query_logs.csv")
    save_csv(query_logs_path, query_logs, header=[
        "key", "query", "found", "reason", "svg_name", "elapsed_s", "hardness", "chart_expected", "chart_predicted"
    ])

    # save summary
    summary_rows = [
        ("timestamp", datetime.utcnow().isoformat()),
        ("total_queries", total),
        ("found", found),
        ("not_found", not_found),
        ("fails", fail_count),
        ("avg_time_s", round(avg_time, 3)),
        ("success_rate_pct", round(success_rate, 3)),
        ("correctCharts_identified", correctCharts)
    ]
    summary_csv_path = os.path.join(LOGS_DIR, "summary.csv")
    save_csv(summary_csv_path, summary_rows, header=["metric", "value"])

    # generate metrics by hardness and save CSV
    per_hardness = []
    for h, counts in hardness_levels.items():
        tot = counts['correct'] + counts['incorrect']
        pct = (counts['correct'] / tot * 100) if tot > 0 else 0.0
        per_hardness.append((h, counts['correct'], counts['incorrect'], tot, round(pct, 3)))
    per_hardness_path = os.path.join(LOGS_DIR, "per_hardness.csv")
    save_csv(per_hardness_path, per_hardness, header=["hardness", "correct", "incorrect", "total", "accuracy_pct"])

    # print summary
    print("\n\n===== SUMMARY =====")
    print(f"Total queries processed: {total}")
    print(f"Found: {found} | Not found: {not_found} | Fails: {fail_count}")
    print(f"Avg elapsed (s): {avg_time:.3f}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Correct chart-type matches (expected in predicted): {correctCharts}")
    print(f"Query logs saved to: {query_logs_path}")
    print(f"Summary saved to: {summary_csv_path}")
    print(f"Per-hardness saved to: {per_hardness_path}")
    print("===================\n\n")


    # save list of errors for inspection
    errors_path = os.path.join(LOGS_DIR, "errors.txt")
    with open(errors_path, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(str(e) + "\n")

    return {
        "total": total,
        "found": found,
        "not_found": not_found,
        "fails": fail_count,
        "avg_time": avg_time,
        "success_rate": success_rate,
        "correctCharts": correctCharts,
        "query_logs_path": query_logs_path,
        "summary_csv_path": summary_csv_path,
        "per_hardness_path": per_hardness_path,
        "errors_path": errors_path
    }



# run this script)
if __name__ == "__main__":
    # adjust path to your JSON file
    with open("visEval_dataset/visEval_single.json", "r", encoding="utf-8") as f:
        dados = json.load(f)

    agent = ChartGeneratorAgent()
    stats = extract_numbers(dados, agent)  # adjust limit as needed

    print("Final result:", stats)