import pandas as pd
from typing import Dict, Any, Optional

class XERParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tables: Dict[str, pd.DataFrame] = {}

    def parse(self) -> Dict[str, pd.DataFrame]:
        """Parses the XER file into a dictionary of pandas DataFrames."""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"XER file not found: {self.file_path}")

        current_table = None
        current_headers = []
        table_data = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('%T'):
                # Save previous table
                if current_table and current_headers:
                    self.tables[current_table] = pd.DataFrame(table_data, columns=current_headers)

                parts = line.split('\t')
                if len(parts) > 1:
                    current_table = parts[1]
                current_headers = []
                table_data = []

            elif line.startswith('%F'):
                parts = line.split('\t')
                current_headers = parts[1:]

            elif line.startswith('%R'):
                parts = line.split('\t')
                # Ensure the row has the same number of columns as the headers
                row = parts[1:]
                if len(row) < len(current_headers):
                    row.extend([''] * (len(current_headers) - len(row)))
                elif len(row) > len(current_headers):
                    row = row[:len(current_headers)]
                table_data.append(row)

        # Save last table
        if current_table and current_headers:
            self.tables[current_table] = pd.DataFrame(table_data, columns=current_headers)

        return self.tables

    def run_dcma_14_point_check(self) -> Dict[str, Any]:
        """Runs a mock DCMA 14-point schedule assessment."""
        tasks = self.tables.get('TASK', pd.DataFrame())
        preds = self.tables.get('TASKPRED', pd.DataFrame())

        if tasks.empty:
            return {
                "total_activities": 0,
                "dcma_checks": {
                    "logic_missing_pct": 0.0,
                    "negative_float_pct": 0.0,
                    "high_float_pct": 0.0,
                    "invalid_dates_pct": 0.0,
                    "resource_missing_pct": 0.0,
                    "hard_constraints_pct": 0.0,
                    "passed_audit": False,
                    "details": {"error": "No tasks found in XER"}
                }
            }

        total_tasks = len(tasks)
        missing_logic_count = 0

        # Point 1: Logic
        if not preds.empty and 'task_id' in tasks.columns and 'pred_task_id' in preds.columns and 'succ_task_id' in preds.columns:
            has_pred = tasks['task_id'].isin(preds['succ_task_id'])
            has_succ = tasks['task_id'].isin(preds['pred_task_id'])
            missing_logic_count = (~(has_pred | has_succ)).sum()

        logic_missing_pct = (missing_logic_count / total_tasks) * 100 if total_tasks > 0 else 0.0

        # Mock values for the rest of the 14 points
        negative_float_pct = 0.0
        high_float_pct = 0.0
        invalid_dates_pct = 0.0
        resource_missing_pct = 0.0
        hard_constraints_pct = 0.0

        passed = logic_missing_pct <= 5.0

        return {
            "total_activities": total_tasks,
            "dcma_checks": {
                "logic_missing_pct": float(logic_missing_pct),
                "negative_float_pct": negative_float_pct,
                "high_float_pct": high_float_pct,
                "invalid_dates_pct": invalid_dates_pct,
                "resource_missing_pct": resource_missing_pct,
                "hard_constraints_pct": hard_constraints_pct,
                "passed_audit": passed,
                "details": {"missing_logic_count": int(missing_logic_count)}
            }
        }
