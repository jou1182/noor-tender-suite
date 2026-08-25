import pandas as pd
import json
from typing import List
from app.models.tender_models import ComplianceRecord

class ReportGenerator:
    @staticmethod
    def generate_json_report(records: List[ComplianceRecord]) -> str:
        data = [
            {
                "clause_code": r.clause_code,
                "requirement": r.requirement,
                "status": r.status,
                "severity": r.severity,
                "gap_analysis": r.gap_analysis
            } for r in records
        ]
        return json.dumps(data, indent=2)

    @staticmethod
    def generate_excel_matrix(records: List[ComplianceRecord], output_path: str):
        data = [
            {
                "Clause Code": r.clause_code,
                "Requirement": r.requirement,
                "Status": r.status,
                "Severity": r.severity,
                "Gap Analysis": r.gap_analysis
            } for r in records
        ]
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Compliance Matrix', index=False)
            
            workbook  = writer.book
            worksheet = writer.sheets['Compliance Matrix']
            
            # Format columns
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 40)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 40)

            # Conditional formatting for Pass/Fail
            pass_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            fail_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            
            worksheet.conditional_format('C2:C1000', {'type': 'cell',
                                                      'criteria': 'equal to',
                                                      'value': '"Compliant"',
                                                      'format': pass_format})
            worksheet.conditional_format('C2:C1000', {'type': 'cell',
                                                      'criteria': 'equal to',
                                                      'value': '"Non-Compliant"',
                                                      'format': fail_format})
